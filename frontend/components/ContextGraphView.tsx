"use client";

import { useEffect, useRef, useCallback, useMemo, useState } from "react";
import { Box, Text, Flex, Badge } from "@chakra-ui/react";
import type { GraphData } from "@/lib/api";

// NVL types
interface NvlNode {
  id: string;
  caption?: string;
  color?: string;
  size?: number;
}

interface NvlRelationship {
  id: string;
  from: string;
  to: string;
  caption?: string;
  color?: string;
}

// Node color mapping by label
const NODE_COLORS: Record<string, string> = {
  Person: "#4299E1",
  Account: "#48BB78",
  Transaction: "#ED8936",
  Decision: "#9F7AEA",
  Organization: "#F56565",
  Policy: "#38B2AC",
  Exception: "#D69E2E",
  Escalation: "#805AD5",
  Employee: "#63B3ED",
  DecisionContext: "#B794F4",
  Precedent: "#F687B3",
};

// Node size by label
const NODE_SIZES: Record<string, number> = {
  Decision: 30,
  Person: 25,
  Account: 22,
  Transaction: 18,
  Organization: 25,
  Policy: 22,
  Exception: 20,
  Escalation: 20,
  Employee: 22,
  DecisionContext: 18,
  Precedent: 18,
};

interface ContextGraphViewProps {
  graphData: GraphData | null;
  onNodeClick?: (nodeId: string, labels: string[]) => void;
  selectedNodeId?: string;
  height?: string;
  showLegend?: boolean;
}

export function ContextGraphView({
  graphData,
  onNodeClick,
  selectedNodeId,
  height = "100%",
  showLegend = true,
}: ContextGraphViewProps) {
  // Transform graph data to NVL format
  const nvlData = useMemo(() => {
    if (!graphData) return { nodes: [], relationships: [] };

    const nodes: NvlNode[] = graphData.nodes.map((node) => {
      const primaryLabel = node.labels[0] || "Unknown";
      const caption =
        (node.properties.name as string) ||
        (node.properties.first_name as string) ||
        (node.properties.decision_type as string) ||
        node.id.slice(0, 8);

      return {
        id: node.id,
        caption,
        color:
          selectedNodeId === node.id
            ? "#E53E3E"
            : NODE_COLORS[primaryLabel] || "#718096",
        size: NODE_SIZES[primaryLabel] || 20,
      };
    });

    const relationships: NvlRelationship[] = graphData.relationships.map(
      (rel) => ({
        id: rel.id,
        from: rel.startNodeId,
        to: rel.endNodeId,
        caption: rel.type,
        color:
          rel.type === "CAUSED"
            ? "#E53E3E"
            : rel.type === "INFLUENCED"
              ? "#D69E2E"
              : "#A0AEC0",
      }),
    );

    return { nodes, relationships };
  }, [graphData, selectedNodeId]);

  const handleNodeClick = useCallback(
    (node: NvlNode) => {
      if (onNodeClick && graphData) {
        const originalNode = graphData.nodes.find((n) => n.id === node.id);
        if (originalNode) {
          onNodeClick(node.id, originalNode.labels);
        }
      }
    },
    [onNodeClick, graphData],
  );

  if (!graphData || graphData.nodes.length === 0) {
    return (
      <Flex
        h={height}
        align="center"
        justify="center"
        direction="column"
        gap={4}
        p={8}
      >
        <Text color="gray.500" textAlign="center">
          No graph data to display.
        </Text>
        <Text color="gray.400" fontSize="sm" textAlign="center">
          Use the AI assistant to search for customers or decisions to visualize
          the context graph.
        </Text>
      </Flex>
    );
  }

  return (
    <Box h={height} position="relative">
      {/* Legend */}
      {showLegend && (
        <Flex
          position="absolute"
          top={2}
          left={2}
          zIndex={10}
          bg="bg.surface"
          borderRadius="md"
          p={2}
          gap={2}
          flexWrap="wrap"
          maxW="200px"
          boxShadow="sm"
          borderWidth="1px"
          borderColor="border.default"
        >
          {Object.entries(NODE_COLORS)
            .slice(0, 6)
            .map(([label, color]) => (
              <Badge
                key={label}
                size="sm"
                style={{ backgroundColor: color, color: "white" }}
              >
                {label}
              </Badge>
            ))}
        </Flex>
      )}

      {/* Graph Container */}
      <Box h="100%" w="100%">
        <NvlGraph
          nodes={nvlData.nodes}
          relationships={nvlData.relationships}
          onNodeClick={handleNodeClick}
        />
      </Box>
    </Box>
  );
}

// Separate component for NVL to handle dynamic import properly
function NvlGraph({
  nodes,
  relationships,
  onNodeClick,
}: {
  nodes: NvlNode[];
  relationships: NvlRelationship[];
  onNodeClick: (node: NvlNode) => void;
}) {
  const [NvlComponent, setNvlComponent] =
    useState<React.ComponentType<any> | null>(null);

  useEffect(() => {
    import("@neo4j-nvl/react").then((mod) => {
      setNvlComponent(() => mod.InteractiveNvlWrapper);
    });
  }, []);

  if (!NvlComponent) {
    return (
      <Flex h="100%" align="center" justify="center">
        <Text color="gray.500">Loading graph visualization...</Text>
      </Flex>
    );
  }

  return (
    <NvlComponent
      nodes={nodes}
      rels={relationships}
      nvlOptions={{
        layout: "d3Force",
        initialZoom: 1,
        minZoom: 0.1,
        maxZoom: 3,
      }}
      nvlCallbacks={{
        onNodeClick: (node: NvlNode) => onNodeClick(node),
      }}
      style={{ width: "100%", height: "100%" }}
    />
  );
}

// Compact inline graph for chat messages
interface InlineGraphProps {
  graphData: GraphData;
  height?: string;
  onNodeClick?: (nodeId: string, labels: string[]) => void;
}

export function InlineGraph({
  graphData,
  height = "200px",
  onNodeClick,
}: InlineGraphProps) {
  return (
    <Box
      borderRadius="md"
      borderWidth="1px"
      borderColor="border.default"
      overflow="hidden"
      h={height}
      my={2}
    >
      <ContextGraphView
        graphData={graphData}
        onNodeClick={onNodeClick}
        showLegend={false}
        height={height}
      />
    </Box>
  );
}
