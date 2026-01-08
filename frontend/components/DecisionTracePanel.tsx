'use client';

import { useState, useEffect } from 'react';
import {
  Box,
  Text,
  Flex,
  Badge,
  VStack,
  HStack,
  Heading,
  Separator,
  Spinner,
} from '@chakra-ui/react';
import {
  getSimilarDecisions,
  getCausalChain,
  type Decision,
  type SimilarDecision,
  type CausalChain,
} from '@/lib/api';

interface DecisionTracePanelProps {
  decision: Decision | null;
  onDecisionSelect: (decision: Decision) => void;
}

const DECISION_TYPE_COLORS: Record<string, string> = {
  credit_approval: 'green',
  credit_denial: 'red',
  fraud_alert: 'red',
  fraud_cleared: 'green',
  trading_approval: 'blue',
  trading_halt: 'orange',
  exception_granted: 'yellow',
  exception_denied: 'red',
  escalation: 'purple',
};

export function DecisionTracePanel({ decision, onDecisionSelect }: DecisionTracePanelProps) {
  const [similarDecisions, setSimilarDecisions] = useState<SimilarDecision[]>([]);
  const [causalChain, setCausalChain] = useState<CausalChain | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!decision) {
      setSimilarDecisions([]);
      setCausalChain(null);
      return;
    }

    const fetchData = async () => {
      setLoading(true);
      try {
        const [similar, chain] = await Promise.all([
          getSimilarDecisions(decision.id, 5, 'hybrid'),
          getCausalChain(decision.id, 2),
        ]);
        setSimilarDecisions(similar);
        setCausalChain(chain);
      } catch (error) {
        console.error('Failed to fetch decision data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [decision]);

  if (!decision) {
    return (
      <Flex h="100%" align="center" justify="center" p={8}>
        <Text color="gray.500" textAlign="center">
          Select a decision from the chat or graph to view its trace.
        </Text>
      </Flex>
    );
  }

  const typeColor = DECISION_TYPE_COLORS[decision.decision_type] || 'gray';

  return (
    <Box p={4} h="100%" overflow="auto">
      <VStack gap={4} align="stretch">
        {/* Decision Header */}
        <Box>
          <HStack gap={2} mb={2}>
            <Badge colorPalette={typeColor} size="lg">
              {decision.decision_type.replace(/_/g, ' ')}
            </Badge>
            <Badge colorPalette={decision.status === 'final' ? 'green' : 'yellow'}>
              {decision.status}
            </Badge>
          </HStack>
          <Text fontSize="sm" color="gray.500">
            {new Date(decision.timestamp).toLocaleString()} • {decision.made_by}
          </Text>
        </Box>

        <Separator />

        {/* Reasoning */}
        <Box>
          <Heading size="sm" mb={2}>
            Reasoning
          </Heading>
          <Box
            bg="bg.subtle"
            p={3}
            borderRadius="md"
            fontSize="sm"
            whiteSpace="pre-wrap"
          >
            {decision.reasoning}
          </Box>
        </Box>

        {/* Outcome & Confidence */}
        <HStack gap={4}>
          <Box flex={1}>
            <Text fontSize="xs" color="gray.500" mb={1}>
              Outcome
            </Text>
            <Text fontWeight="medium">{decision.outcome}</Text>
          </Box>
          <Box>
            <Text fontSize="xs" color="gray.500" mb={1}>
              Confidence
            </Text>
            <Text fontWeight="medium">{(decision.confidence * 100).toFixed(0)}%</Text>
          </Box>
        </HStack>

        {/* Risk Factors */}
        {decision.risk_factors && decision.risk_factors.length > 0 && (
          <Box>
            <Heading size="sm" mb={2}>
              Risk Factors
            </Heading>
            <Flex gap={2} flexWrap="wrap">
              {decision.risk_factors.map((factor, idx) => (
                <Badge key={idx} colorPalette="orange" variant="subtle">
                  {factor}
                </Badge>
              ))}
            </Flex>
          </Box>
        )}

        <Separator />

        {/* Causal Chain */}
        <Box>
          <Heading size="sm" mb={2}>
            Causal Chain
          </Heading>
          {loading ? (
            <Flex justify="center" py={4}>
              <Spinner size="sm" />
            </Flex>
          ) : causalChain ? (
            <VStack gap={2} align="stretch">
              {/* Causes */}
              {causalChain.causes.length > 0 && (
                <Box>
                  <Text fontSize="xs" color="gray.500" mb={1}>
                    Caused by ({causalChain.causes.length})
                  </Text>
                  {causalChain.causes.map((cause) => (
                    <DecisionCard
                      key={cause.id}
                      decision={cause}
                      onClick={() => onDecisionSelect(cause)}
                      direction="cause"
                    />
                  ))}
                </Box>
              )}

              {/* Effects */}
              {causalChain.effects.length > 0 && (
                <Box>
                  <Text fontSize="xs" color="gray.500" mb={1}>
                    Led to ({causalChain.effects.length})
                  </Text>
                  {causalChain.effects.map((effect) => (
                    <DecisionCard
                      key={effect.id}
                      decision={effect}
                      onClick={() => onDecisionSelect(effect)}
                      direction="effect"
                    />
                  ))}
                </Box>
              )}

              {causalChain.causes.length === 0 && causalChain.effects.length === 0 && (
                <Text fontSize="sm" color="gray.500">
                  No causal relationships found.
                </Text>
              )}
            </VStack>
          ) : (
            <Text fontSize="sm" color="gray.500">
              No causal chain data.
            </Text>
          )}
        </Box>

        <Separator />

        {/* Similar Decisions */}
        <Box>
          <Heading size="sm" mb={2}>
            Similar Decisions (Hybrid Search)
          </Heading>
          {loading ? (
            <Flex justify="center" py={4}>
              <Spinner size="sm" />
            </Flex>
          ) : similarDecisions.length > 0 ? (
            <VStack gap={2} align="stretch">
              {similarDecisions.map((similar) => (
                <SimilarDecisionCard
                  key={similar.decision.id}
                  similarDecision={similar}
                  onClick={() => onDecisionSelect(similar.decision)}
                />
              ))}
            </VStack>
          ) : (
            <Text fontSize="sm" color="gray.500">
              No similar decisions found.
            </Text>
          )}
        </Box>
      </VStack>
    </Box>
  );
}

// Decision card for causal chain
function DecisionCard({
  decision,
  onClick,
  direction,
}: {
  decision: Decision;
  onClick: () => void;
  direction: 'cause' | 'effect';
}) {
  const typeColor = DECISION_TYPE_COLORS[decision.decision_type] || 'gray';
  const arrow = direction === 'cause' ? '↑' : '↓';

  return (
    <Box
      bg="bg.subtle"
      p={2}
      borderRadius="md"
      cursor="pointer"
      _hover={{ bg: 'bg.emphasized' }}
      onClick={onClick}
      mb={1}
    >
      <HStack gap={2}>
        <Text color={direction === 'cause' ? 'blue.500' : 'green.500'}>{arrow}</Text>
        <Badge size="sm" colorPalette={typeColor}>
          {decision.decision_type.replace(/_/g, ' ')}
        </Badge>
        <Text fontSize="xs" color="gray.500" flex={1} isTruncated>
          {decision.outcome}
        </Text>
      </HStack>
    </Box>
  );
}

// Similar decision card with similarity score
function SimilarDecisionCard({
  similarDecision,
  onClick,
}: {
  similarDecision: SimilarDecision;
  onClick: () => void;
}) {
  const { decision, similarity_score, similarity_type } = similarDecision;
  const typeColor = DECISION_TYPE_COLORS[decision.decision_type] || 'gray';

  return (
    <Box
      bg="bg.subtle"
      p={3}
      borderRadius="md"
      cursor="pointer"
      _hover={{ bg: 'bg.emphasized' }}
      onClick={onClick}
    >
      <HStack justify="space-between" mb={1}>
        <Badge size="sm" colorPalette={typeColor}>
          {decision.decision_type.replace(/_/g, ' ')}
        </Badge>
        <HStack gap={1}>
          <Badge size="sm" variant="outline">
            {similarity_type}
          </Badge>
          <Text fontSize="xs" fontWeight="bold" color="brand.500">
            {(similarity_score * 100).toFixed(0)}%
          </Text>
        </HStack>
      </HStack>
      <Text fontSize="sm" color="gray.600" noOfLines={2}>
        {decision.reasoning.slice(0, 150)}...
      </Text>
      <Text fontSize="xs" color="gray.400" mt={1}>
        {new Date(decision.timestamp).toLocaleDateString()}
      </Text>
    </Box>
  );
}
