'use client';

import { useState, useCallback } from 'react';
import {
  Box,
  Flex,
  Heading,
  Text,
  Container,
  Grid,
  GridItem,
} from '@chakra-ui/react';
import dynamic from 'next/dynamic';
import { ChatInterface } from '@/components/ChatInterface';
import { DecisionTracePanel } from '@/components/DecisionTracePanel';
import type { Decision, GraphData, ChatMessage } from '@/lib/api';

// Dynamic import for NVL to avoid SSR issues
const ContextGraphView = dynamic(
  () => import('@/components/ContextGraphView').then((mod) => mod.ContextGraphView),
  { ssr: false }
);

export default function Home() {
  const [selectedDecision, setSelectedDecision] = useState<Decision | null>(null);
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [conversationHistory, setConversationHistory] = useState<ChatMessage[]>([]);

  const handleDecisionSelect = useCallback((decision: Decision) => {
    setSelectedDecision(decision);
  }, []);

  const handleGraphUpdate = useCallback((data: GraphData) => {
    setGraphData(data);
  }, []);

  const handleNodeClick = useCallback((nodeId: string, labels: string[]) => {
    console.log('Node clicked:', nodeId, labels);
    // Could trigger loading decision details if it's a Decision node
  }, []);

  return (
    <Box minH="100vh" bg="bg.canvas">
      {/* Header */}
      <Box
        as="header"
        bg="bg.surface"
        borderBottomWidth="1px"
        borderColor="border.default"
        py={4}
        px={6}
      >
        <Container maxW="container.2xl">
          <Flex justify="space-between" align="center">
            <Box>
              <Heading size="lg" color="brand.600">
                Context Graph Demo
              </Heading>
              <Text color="gray.500" fontSize="sm">
                AI-powered decision tracing for financial institutions
              </Text>
            </Box>
          </Flex>
        </Container>
      </Box>

      {/* Main Content */}
      <Container maxW="container.2xl" py={6}>
        <Grid
          templateColumns={{ base: '1fr', lg: '1fr 1fr', xl: '1fr 1.5fr 1fr' }}
          gap={6}
          h="calc(100vh - 140px)"
        >
          {/* Chat Panel */}
          <GridItem>
            <Box
              bg="bg.surface"
              borderRadius="lg"
              borderWidth="1px"
              borderColor="border.default"
              h="100%"
              overflow="hidden"
              display="flex"
              flexDirection="column"
            >
              <Box p={4} borderBottomWidth="1px" borderColor="border.default">
                <Heading size="md">AI Assistant</Heading>
                <Text fontSize="sm" color="gray.500">
                  Ask questions about customers, decisions, and policies
                </Text>
              </Box>
              <Box flex="1" overflow="hidden">
                <ChatInterface
                  conversationHistory={conversationHistory}
                  onConversationUpdate={setConversationHistory}
                  onDecisionSelect={handleDecisionSelect}
                  onGraphUpdate={handleGraphUpdate}
                />
              </Box>
            </Box>
          </GridItem>

          {/* Graph Visualization */}
          <GridItem display={{ base: 'none', xl: 'block' }}>
            <Box
              bg="bg.surface"
              borderRadius="lg"
              borderWidth="1px"
              borderColor="border.default"
              h="100%"
              overflow="hidden"
            >
              <Box p={4} borderBottomWidth="1px" borderColor="border.default">
                <Heading size="md">Context Graph</Heading>
                <Text fontSize="sm" color="gray.500">
                  Visualize entities, decisions, and causal relationships
                </Text>
              </Box>
              <Box h="calc(100% - 80px)">
                <ContextGraphView
                  graphData={graphData}
                  onNodeClick={handleNodeClick}
                  selectedNodeId={selectedDecision?.id}
                />
              </Box>
            </Box>
          </GridItem>

          {/* Decision Trace Panel */}
          <GridItem>
            <Box
              bg="bg.surface"
              borderRadius="lg"
              borderWidth="1px"
              borderColor="border.default"
              h="100%"
              overflow="hidden"
            >
              <Box p={4} borderBottomWidth="1px" borderColor="border.default">
                <Heading size="md">Decision Trace</Heading>
                <Text fontSize="sm" color="gray.500">
                  Inspect reasoning, precedents, and causal chains
                </Text>
              </Box>
              <Box h="calc(100% - 80px)" overflow="auto">
                <DecisionTracePanel
                  decision={selectedDecision}
                  onDecisionSelect={handleDecisionSelect}
                />
              </Box>
            </Box>
          </GridItem>
        </Grid>
      </Container>
    </Box>
  );
}
