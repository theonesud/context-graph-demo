"use client";

import { useEffect, useState } from "react";
import {
  Box,
  Button,
  CloseButton,
  Drawer,
  Heading,
  Portal,
  Text,
  VStack,
  Badge,
  Separator,
  HStack,
} from "@chakra-ui/react";
import dynamic from "next/dynamic";
import { getGraphSchema, schemaToGraphData, type GraphData } from "@/lib/api";

// Dynamic import for NVL to avoid SSR issues
const ContextGraphView = dynamic(
  () =>
    import("@/components/ContextGraphView").then((mod) => mod.ContextGraphView),
  { ssr: false },
);

interface SchemaDrawerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function SchemaDrawer({ open, onOpenChange }: SchemaDrawerProps) {
  const [schemaData, setSchemaData] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(false);

  // Load schema when drawer opens
  useEffect(() => {
    if (open && !schemaData) {
      setLoading(true);
      getGraphSchema()
        .then((schema) => {
          const data = schemaToGraphData(schema);
          setSchemaData(data);
        })
        .catch((error) => {
          console.error("Failed to load graph schema:", error);
        })
        .finally(() => {
          setLoading(false);
        });
    }
  }, [open, schemaData]);

  return (
    <Drawer.Root
      open={open}
      onOpenChange={(e) => onOpenChange(e.open)}
      placement="end"
      size="lg"
    >
      <Portal>
        <Drawer.Backdrop />
        <Drawer.Positioner>
          <Drawer.Content>
            <Drawer.Header borderBottomWidth="1px">
              <Drawer.Title>About Context Graph</Drawer.Title>
              <Drawer.CloseTrigger asChild>
                <CloseButton size="sm" />
              </Drawer.CloseTrigger>
            </Drawer.Header>
            <Drawer.Body>
              <VStack gap={6} align="stretch">
                {/* Overview Section */}
                <Box>
                  <Heading size="md" mb={3}>
                    Overview
                  </Heading>
                  <Text color="gray.600" mb={3}>
                    Context Graph is an AI-powered decision tracing system
                    designed for financial institutions. It captures, stores,
                    and analyzes the reasoning behind every decision made by AI
                    agents and human operators.
                  </Text>
                  <Text color="gray.600" mb={4}>
                    Using a knowledge graph powered by Neo4j, the system
                    maintains full context and provenance for decisions,
                    enabling transparency, auditability, and continuous
                    improvement.
                  </Text>

                  {/* Neo4j Branding and Blog Link */}
                  <Box
                    p={4}
                    bg="blue.50"
                    _dark={{ bg: "blue.900" }}
                    borderRadius="lg"
                    borderWidth="1px"
                    borderColor="blue.200"
                    _darkBorderColor={{ borderColor: "blue.700" }}
                  >
                    <HStack gap={3} mb={3}>
                      <Box
                        as="svg"
                        viewBox="0 0 100 100"
                        width="36px"
                        height="36px"
                        flexShrink={0}
                      >
                        <circle cx="50" cy="50" r="48" fill="#018BFF" />
                        <g fill="white">
                          <circle cx="50" cy="30" r="8" />
                          <circle cx="30" cy="65" r="8" />
                          <circle cx="70" cy="65" r="8" />
                          <line
                            x1="50"
                            y1="38"
                            x2="33"
                            y2="58"
                            stroke="white"
                            strokeWidth="3"
                          />
                          <line
                            x1="50"
                            y1="38"
                            x2="67"
                            y2="58"
                            stroke="white"
                            strokeWidth="3"
                          />
                          <line
                            x1="38"
                            y1="65"
                            x2="62"
                            y2="65"
                            stroke="white"
                            strokeWidth="3"
                          />
                        </g>
                      </Box>
                      <Box>
                        <Text
                          fontWeight="semibold"
                          color="blue.700"
                          _dark={{ color: "blue.200" }}
                        >
                          Powered by Neo4j
                        </Text>
                        <Text
                          fontSize="sm"
                          color="gray.600"
                          _dark={{ color: "gray.400" }}
                        >
                          The graph intelligence platform
                        </Text>
                      </Box>
                    </HStack>
                    <Button
                      asChild
                      size="sm"
                      colorPalette="blue"
                      variant="outline"
                      width="full"
                    >
                      <a
                        href="https://neo4j.com/blog/genai/hands-on-with-context-graphs-and-neo4j/"
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        Read the Context Graph Blog Post
                      </a>
                    </Button>
                  </Box>
                </Box>

                <Separator />

                {/* How It Works Section */}
                <Box>
                  <Heading size="md" mb={3}>
                    How It Works
                  </Heading>
                  <VStack gap={3} align="stretch">
                    <FeatureItem
                      number="1"
                      title="Ask the AI Assistant"
                      description="Use natural language to search for customers, review decisions, or analyze patterns. The AI has access to the full context graph."
                    />
                    <FeatureItem
                      number="2"
                      title="Explore the Context Graph"
                      description="Visualize entities and their relationships. Double-click nodes to expand and explore connected data. Click nodes to inspect properties."
                    />
                    <FeatureItem
                      number="3"
                      title="Trace Decisions"
                      description="Select any decision to see its full reasoning, causal chain, and similar precedents. Understand why decisions were made."
                    />
                    <FeatureItem
                      number="4"
                      title="Find Patterns"
                      description="Use graph algorithms to detect fraud patterns, find similar decisions, and identify influential precedents across the organization."
                    />
                  </VStack>
                </Box>

                <Separator />

                {/* Key Features Section */}
                <Box>
                  <Heading size="md" mb={3}>
                    Key Features
                  </Heading>
                  <HStack gap={2} flexWrap="wrap">
                    <Badge colorPalette="blue" size="lg">
                      Decision Traces
                    </Badge>
                    <Badge colorPalette="green" size="lg">
                      Causal Chains
                    </Badge>
                    <Badge colorPalette="purple" size="lg">
                      Semantic Search
                    </Badge>
                    <Badge colorPalette="orange" size="lg">
                      Graph Analytics
                    </Badge>
                    <Badge colorPalette="cyan" size="lg">
                      Fraud Detection
                    </Badge>
                    <Badge colorPalette="pink" size="lg">
                      Precedent Matching
                    </Badge>
                  </HStack>
                </Box>

                <Separator />

                {/* Graph Schema Section */}
                <Box>
                  <Heading size="md" mb={3}>
                    Graph Schema
                  </Heading>
                  <Text color="gray.600" mb={4}>
                    The context graph contains the following entity types and
                    their relationships. This schema visualization shows how
                    data is connected in the knowledge graph.
                  </Text>
                  <Box
                    h="350px"
                    borderRadius="md"
                    borderWidth="1px"
                    borderColor="border.default"
                    overflow="hidden"
                    bg="bg.subtle"
                  >
                    {loading ? (
                      <Box
                        h="100%"
                        display="flex"
                        alignItems="center"
                        justifyContent="center"
                      >
                        <Text color="gray.500">Loading schema...</Text>
                      </Box>
                    ) : schemaData ? (
                      <ContextGraphView
                        graphData={schemaData}
                        height="100%"
                        showLegend={false}
                      />
                    ) : (
                      <Box
                        h="100%"
                        display="flex"
                        alignItems="center"
                        justifyContent="center"
                      >
                        <Text color="gray.500">
                          Failed to load schema. Please try again.
                        </Text>
                      </Box>
                    )}
                  </Box>
                </Box>

                <Separator />

                {/* Entity Types Section */}
                <Box>
                  <Heading size="md" mb={3}>
                    Entity Types
                  </Heading>
                  <VStack gap={2} align="stretch">
                    <EntityType
                      name="Decision"
                      color="purple"
                      description="AI and human decisions with full reasoning traces"
                    />
                    <EntityType
                      name="Person"
                      color="blue"
                      description="Customers and individuals in the system"
                    />
                    <EntityType
                      name="Account"
                      color="green"
                      description="Financial accounts owned by persons or organizations"
                    />
                    <EntityType
                      name="Transaction"
                      color="orange"
                      description="Financial transactions between accounts"
                    />
                    <EntityType
                      name="Organization"
                      color="red"
                      description="Companies, employers, and counterparties"
                    />
                    <EntityType
                      name="Alert"
                      color="yellow"
                      description="Fraud alerts and compliance notifications"
                    />
                    <EntityType
                      name="SupportTicket"
                      color="cyan"
                      description="Customer support tickets and inquiries"
                    />
                    <EntityType
                      name="Policy"
                      color="teal"
                      description="Business rules and compliance policies"
                    />
                    <EntityType
                      name="Employee"
                      color="blue"
                      description="Internal staff who make or review decisions"
                    />
                  </VStack>
                </Box>
              </VStack>
            </Drawer.Body>
          </Drawer.Content>
        </Drawer.Positioner>
      </Portal>
    </Drawer.Root>
  );
}

function FeatureItem({
  number,
  title,
  description,
}: {
  number: string;
  title: string;
  description: string;
}) {
  return (
    <HStack gap={3} align="flex-start">
      <Box
        w="24px"
        h="24px"
        borderRadius="full"
        bg="brand.500"
        color="white"
        display="flex"
        alignItems="center"
        justifyContent="center"
        fontSize="sm"
        fontWeight="bold"
        flexShrink={0}
      >
        {number}
      </Box>
      <Box>
        <Text fontWeight="medium">{title}</Text>
        <Text fontSize="sm" color="gray.600">
          {description}
        </Text>
      </Box>
    </HStack>
  );
}

function EntityType({
  name,
  color,
  description,
}: {
  name: string;
  color: string;
  description: string;
}) {
  return (
    <HStack gap={3}>
      <Badge
        colorPalette={color}
        size="sm"
        minW="100px"
        justifyContent="center"
      >
        {name}
      </Badge>
      <Text fontSize="sm" color="gray.600">
        {description}
      </Text>
    </HStack>
  );
}
