"use client";

import { useState, useCallback } from "react";
import {
  Box,
  Flex,
  Heading,
  Text,
  Container,
  Grid,
  GridItem,
  Button,
  Menu,
  Portal,
} from "@chakra-ui/react";
import { LuMenu } from "react-icons/lu";
import dynamic from "next/dynamic";
import { ChatInterface } from "@/components/ChatInterface";
import { DecisionTracePanel } from "@/components/DecisionTracePanel";
import { SchemaDrawer } from "@/components/SchemaDrawer";
import type { Decision, GraphData, GraphNode, ChatMessage } from "@/lib/api";

// Helper to convert a GraphNode to a Decision object
function graphNodeToDecision(node: GraphNode): Decision {
  const props = node.properties;
  return {
    id: (props.id as string) || node.id,
    decision_type: (props.decision_type as string) || "unknown",
    category: (props.category as string) || "unknown",
    reasoning: (props.reasoning as string) || "",
    reasoning_summary: props.reasoning_summary as string | undefined,
    confidence_score: props.confidence_score as number | undefined,
    risk_factors: (props.risk_factors as string[]) || [],
    status: (props.status as string) || "unknown",
    decision_timestamp: props.decision_timestamp as string | undefined,
    timestamp: props.decision_timestamp as string | undefined,
  };
}

// Dynamic import for NVL to avoid SSR issues
const ContextGraphView = dynamic(
  () =>
    import("@/components/ContextGraphView").then((mod) => mod.ContextGraphView),
  { ssr: false },
);

export default function Home() {
  const [selectedDecision, setSelectedDecision] = useState<Decision | null>(
    null,
  );
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [graphDecisions, setGraphDecisions] = useState<Decision[]>([]);
  const [conversationHistory, setConversationHistory] = useState<ChatMessage[]>(
    [],
  );
  const [schemaDrawerOpen, setSchemaDrawerOpen] = useState(true);

  const handleDecisionSelect = useCallback((decision: Decision) => {
    setSelectedDecision(decision);
  }, []);

  const handleGraphUpdate = useCallback((data: GraphData) => {
    setGraphData(data);
  }, []);

  const handleNodeClick = useCallback((nodeId: string, labels: string[]) => {
    console.log("Node clicked:", nodeId, labels);
  }, []);

  // Handle when decision nodes in the graph change
  const handleDecisionNodesChange = useCallback(
    (decisionNodes: GraphNode[]) => {
      const decisions = decisionNodes.map(graphNodeToDecision);
      setGraphDecisions(decisions);
    },
    [],
  );

  // Handle when a decision node is clicked in the graph
  const handleDecisionNodeClick = useCallback((node: GraphNode) => {
    const decision = graphNodeToDecision(node);
    setSelectedDecision(decision);
  }, []);

  return (
    <Box minH="100vh" bg="bg.canvas">
      {/* Schema Drawer */}
      <SchemaDrawer
        open={schemaDrawerOpen}
        onOpenChange={setSchemaDrawerOpen}
      />

      {/* Header */}
      <Box
        as="header"
        bg="bg.surface"
        borderBottomWidth="1px"
        borderColor="border.default"
        py={{ base: 2, md: 4 }}
        px={{ base: 3, md: 6 }}
      >
        <Container maxW="container.2xl">
          <Flex justify="space-between" align="center">
            <Flex align="center" gap={3}>
              {/* Neo4j Logo */}
              <a
                href="https://neo4j.com"
                target="_blank"
                rel="noopener noreferrer"
              >
                <Box
                  as="svg"
                  viewBox="0 0 100 100"
                  width={{ base: "32px", md: "40px" }}
                  height={{ base: "32px", md: "40px" }}
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
              </a>
              <Box>
                <Heading size={{ base: "md", md: "lg" }} color="brand.600">
                  Context Graph Demo
                </Heading>
                <Text
                  color="gray.500"
                  fontSize="sm"
                  display={{ base: "none", md: "block" }}
                >
                  AI-powered decision tracing with Neo4j
                </Text>
              </Box>
            </Flex>

            {/* Desktop Navigation */}
            <Flex gap={2} align="center" display={{ base: "none", md: "flex" }}>
              <Button asChild variant="ghost" size="sm">
                <a
                  href="https://neo4j.com/blog/genai/hands-on-with-context-graphs-and-neo4j/"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Blog Post
                </a>
              </Button>
              <Button asChild variant="ghost" size="sm">
                <a
                  href="https://github.com/johnymontana/context-graph-demo/issues"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Issues
                </a>
              </Button>
              <Button asChild variant="ghost" size="sm">
                <a
                  href="https://github.com/johnymontana/context-graph-demo"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  GitHub
                </a>
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setSchemaDrawerOpen(true)}
              >
                About & Schema
              </Button>
            </Flex>

            {/* Mobile Hamburger Menu */}
            <Box display={{ base: "block", md: "none" }}>
              <Menu.Root>
                <Menu.Trigger asChild>
                  <Button variant="ghost" size="sm">
                    <LuMenu />
                  </Button>
                </Menu.Trigger>
                <Portal>
                  <Menu.Positioner>
                    <Menu.Content>
                      <Menu.Item value="blog" asChild>
                        <a
                          href="https://neo4j.com/blog/genai/hands-on-with-context-graphs-and-neo4j/"
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          Blog Post
                        </a>
                      </Menu.Item>
                      <Menu.Item value="issues" asChild>
                        <a
                          href="https://github.com/johnymontana/context-graph-demo/issues"
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          Issues
                        </a>
                      </Menu.Item>
                      <Menu.Item value="github" asChild>
                        <a
                          href="https://github.com/johnymontana/context-graph-demo"
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          GitHub
                        </a>
                      </Menu.Item>
                      <Menu.Item
                        value="schema"
                        onClick={() => setSchemaDrawerOpen(true)}
                      >
                        About & Schema
                      </Menu.Item>
                    </Menu.Content>
                  </Menu.Positioner>
                </Portal>
              </Menu.Root>
            </Box>
          </Flex>
        </Container>
      </Box>

      {/* Main Content */}
      <Container maxW="container.2xl" py={{ base: 3, md: 6 }}>
        <Grid
          templateColumns={{ base: "1fr", lg: "1fr 1fr", xl: "1fr 1.5fr 1fr" }}
          gap={{ base: 3, md: 6 }}
          h={{ base: "calc(100vh - 60px)", md: "calc(100vh - 140px)" }}
        >
          {/* Chat Panel */}
          <GridItem overflow="hidden">
            <Box
              bg="bg.surface"
              borderRadius="lg"
              borderWidth="1px"
              borderColor="border.default"
              h="100%"
              display="flex"
              flexDirection="column"
              overflow="hidden"
            >
              <Box
                p={4}
                borderBottomWidth="1px"
                borderColor="border.default"
                flexShrink={0}
              >
                <Heading size="md">AI Assistant</Heading>
                <Text fontSize="sm" color="gray.500">
                  Ask questions about customers, decisions, and policies
                </Text>
              </Box>
              <Box flex="1" minH={0} overflow="hidden">
                <ChatInterface
                  conversationHistory={conversationHistory}
                  onConversationUpdate={setConversationHistory}
                  onDecisionSelect={handleDecisionSelect}
                  onGraphUpdate={handleGraphUpdate}
                />
              </Box>
            </Box>
          </GridItem>

          {/* Graph Visualization - Hidden on mobile */}
          <GridItem display={{ base: "none", lg: "block" }} overflow="hidden">
            <Box
              bg="bg.surface"
              borderRadius="lg"
              borderWidth="1px"
              borderColor="border.default"
              h="100%"
              display="flex"
              flexDirection="column"
              overflow="hidden"
            >
              <Box
                p={4}
                borderBottomWidth="1px"
                borderColor="border.default"
                flexShrink={0}
              >
                <Heading size="md">Context Graph</Heading>
                <Text fontSize="sm" color="gray.500">
                  Visualize entities, decisions, and causal relationships
                </Text>
              </Box>
              <Box flex="1" minH={0}>
                <ContextGraphView
                  graphData={graphData}
                  onNodeClick={handleNodeClick}
                  onDecisionNodesChange={handleDecisionNodesChange}
                  onDecisionNodeClick={handleDecisionNodeClick}
                  selectedNodeId={selectedDecision?.id}
                />
              </Box>
            </Box>
          </GridItem>

          {/* Decision Trace Panel */}
          <GridItem display={{ base: "none", xl: "block" }} overflow="hidden">
            <Box
              bg="bg.surface"
              borderRadius="lg"
              borderWidth="1px"
              borderColor="border.default"
              h="100%"
              display="flex"
              flexDirection="column"
              overflow="hidden"
            >
              <Box
                p={4}
                borderBottomWidth="1px"
                borderColor="border.default"
                flexShrink={0}
              >
                <Heading size="md">Decision Trace</Heading>
                <Text fontSize="sm" color="gray.500">
                  Inspect reasoning, precedents, and causal chains
                </Text>
              </Box>
              <Box flex="1" minH={0} overflow="auto">
                <DecisionTracePanel
                  decision={selectedDecision}
                  onDecisionSelect={handleDecisionSelect}
                  graphDecisions={graphDecisions}
                />
              </Box>
            </Box>
          </GridItem>
        </Grid>
      </Container>
    </Box>
  );
}
