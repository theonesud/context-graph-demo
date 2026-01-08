'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import {
  Box,
  Flex,
  Text,
  VStack,
  HStack,
  Badge,
  Spinner,
  Textarea,
  IconButton,
} from '@chakra-ui/react';
import { InlineGraph } from './ContextGraphView';
import {
  sendChatMessage,
  getDecisionGraph,
  type ChatMessage,
  type ChatResponse,
  type Decision,
  type GraphData,
} from '@/lib/api';

interface ChatInterfaceProps {
  conversationHistory: ChatMessage[];
  onConversationUpdate: (messages: ChatMessage[]) => void;
  onDecisionSelect: (decision: Decision) => void;
  onGraphUpdate: (data: GraphData) => void;
}

interface MessageWithGraph extends ChatMessage {
  graphData?: GraphData;
  decision?: Decision;
  toolCalls?: Array<{
    name: string;
    arguments: Record<string, unknown>;
    result?: unknown;
  }>;
}

export function ChatInterface({
  conversationHistory,
  onConversationUpdate,
  onDecisionSelect,
  onGraphUpdate,
}: ChatInterfaceProps) {
  const [messages, setMessages] = useState<MessageWithGraph[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 150)}px`;
    }
  }, [input]);

  const handleSend = useCallback(async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: MessageWithGraph = {
      role: 'user',
      content: input.trim(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response: ChatResponse = await sendChatMessage(
        userMessage.content,
        messages.map((m) => ({ role: m.role, content: m.content }))
      );

      // Build assistant message with graph data if available
      const assistantMessage: MessageWithGraph = {
        role: 'assistant',
        content: response.response,
        toolCalls: response.tool_calls,
        decision: response.decision_trace,
      };

      // If there's a decision trace, fetch the graph data for it
      if (response.decision_trace) {
        try {
          const graphData = await getDecisionGraph(response.decision_trace.id, 2);
          assistantMessage.graphData = graphData;
          onGraphUpdate(graphData);
        } catch (error) {
          console.error('Failed to fetch decision graph:', error);
        }
      }

      // Check tool calls for graph-related results
      if (response.tool_calls) {
        for (const toolCall of response.tool_calls) {
          if (
            toolCall.name.includes('graph') ||
            toolCall.name.includes('decision') ||
            toolCall.name.includes('customer')
          ) {
            // Tool may have returned graph data
            if (toolCall.result && typeof toolCall.result === 'object') {
              const result = toolCall.result as Record<string, unknown>;
              if (result.nodes && result.relationships) {
                assistantMessage.graphData = result as unknown as GraphData;
                onGraphUpdate(result as unknown as GraphData);
              }
            }
          }
        }
      }

      setMessages((prev) => [...prev, assistantMessage]);
      onConversationUpdate([...messages, userMessage, assistantMessage]);

      // If there's a decision, notify parent
      if (response.decision_trace) {
        onDecisionSelect(response.decision_trace);
      }
    } catch (error) {
      console.error('Failed to send message:', error);
      const errorMessage: MessageWithGraph = {
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your request. Please try again.',
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  }, [input, isLoading, messages, onConversationUpdate, onDecisionSelect, onGraphUpdate]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <Flex direction="column" h="100%">
      {/* Messages Area */}
      <Box flex={1} overflow="auto" p={4}>
        <VStack gap={4} align="stretch">
          {/* Welcome message */}
          {messages.length === 0 && (
            <Box
              bg="brand.50"
              _dark={{ bg: 'brand.900' }}
              p={4}
              borderRadius="lg"
              borderWidth="1px"
              borderColor="brand.200"
              _darkBorderColor="brand.700"
            >
              <Text fontWeight="medium" mb={2}>
                Welcome to Context Graph Demo
              </Text>
              <Text fontSize="sm" color="gray.600" _dark={{ color: 'gray.400' }}>
                I can help you search for customers, analyze decisions, find similar precedents,
                and trace causal relationships. Try asking:
              </Text>
              <VStack align="start" mt={3} gap={1}>
                <SuggestionChip
                  text="Search for customer John Smith"
                  onClick={() => setInput('Search for customer John Smith')}
                />
                <SuggestionChip
                  text="Should we approve a $50K credit increase for account #12345?"
                  onClick={() =>
                    setInput('Should we approve a $50K credit increase for account #12345?')
                  }
                />
                <SuggestionChip
                  text="Analyze fraud patterns for suspicious transactions"
                  onClick={() => setInput('Analyze fraud patterns for suspicious transactions')}
                />
              </VStack>
            </Box>
          )}

          {/* Chat messages */}
          {messages.map((message, idx) => (
            <ChatMessageBubble
              key={idx}
              message={message}
              onDecisionClick={onDecisionSelect}
              onNodeClick={(nodeId, labels) => {
                console.log('Node clicked in chat:', nodeId, labels);
              }}
            />
          ))}

          {/* Loading indicator */}
          {isLoading && (
            <Flex align="center" gap={2} p={3}>
              <Spinner size="sm" color="brand.500" />
              <Text fontSize="sm" color="gray.500">
                Thinking...
              </Text>
            </Flex>
          )}

          <div ref={messagesEndRef} />
        </VStack>
      </Box>

      {/* Input Area */}
      <Box p={4} borderTopWidth="1px" borderColor="border.default">
        <Flex gap={2}>
          <Textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about customers, decisions, or policies..."
            rows={1}
            resize="none"
            flex={1}
            disabled={isLoading}
          />
          <IconButton
            aria-label="Send message"
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
            colorPalette="brand"
          >
            <SendIcon />
          </IconButton>
        </Flex>
      </Box>
    </Flex>
  );
}

// Chat message bubble component
function ChatMessageBubble({
  message,
  onDecisionClick,
  onNodeClick,
}: {
  message: MessageWithGraph;
  onDecisionClick: (decision: Decision) => void;
  onNodeClick: (nodeId: string, labels: string[]) => void;
}) {
  const isUser = message.role === 'user';

  return (
    <Box
      alignSelf={isUser ? 'flex-end' : 'flex-start'}
      maxW="85%"
      w={message.graphData ? '100%' : 'auto'}
    >
      <Box
        bg={isUser ? 'brand.500' : 'bg.subtle'}
        color={isUser ? 'white' : 'inherit'}
        px={4}
        py={3}
        borderRadius="lg"
        borderBottomRightRadius={isUser ? 'sm' : 'lg'}
        borderBottomLeftRadius={isUser ? 'lg' : 'sm'}
      >
        {/* Tool calls indicator */}
        {message.toolCalls && message.toolCalls.length > 0 && (
          <HStack gap={1} mb={2} flexWrap="wrap">
            {message.toolCalls.map((tool, idx) => (
              <Badge key={idx} size="sm" colorPalette="purple" variant="subtle">
                {tool.name.replace('mcp__graph__', '')}
              </Badge>
            ))}
          </HStack>
        )}

        {/* Message content */}
        <Text whiteSpace="pre-wrap" fontSize="sm">
          {message.content}
        </Text>

        {/* Decision trace badge */}
        {message.decision && (
          <Box
            mt={3}
            p={2}
            bg={isUser ? 'brand.600' : 'bg.surface'}
            borderRadius="md"
            cursor="pointer"
            onClick={() => onDecisionClick(message.decision!)}
            _hover={{ opacity: 0.8 }}
          >
            <HStack gap={2}>
              <Badge colorPalette="purple" size="sm">
                Decision Recorded
              </Badge>
              <Text fontSize="xs" color={isUser ? 'brand.100' : 'gray.500'}>
                {message.decision.decision_type.replace(/_/g, ' ')}
              </Text>
            </HStack>
          </Box>
        )}
      </Box>

      {/* Inline graph visualization */}
      {message.graphData && message.graphData.nodes.length > 0 && (
        <Box mt={2}>
          <InlineGraph
            graphData={message.graphData}
            height="250px"
            onNodeClick={onNodeClick}
          />
          <Text fontSize="xs" color="gray.500" mt={1}>
            {message.graphData.nodes.length} nodes, {message.graphData.relationships.length}{' '}
            relationships
          </Text>
        </Box>
      )}
    </Box>
  );
}

// Suggestion chip component
function SuggestionChip({ text, onClick }: { text: string; onClick: () => void }) {
  return (
    <Text
      fontSize="sm"
      color="brand.600"
      cursor="pointer"
      _hover={{ textDecoration: 'underline' }}
      onClick={onClick}
    >
      → {text}
    </Text>
  );
}

// Send icon component
function SendIcon() {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      width="20"
      height="20"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <line x1="22" y1="2" x2="11" y2="13" />
      <polygon points="22 2 15 22 11 13 2 9 22 2" />
    </svg>
  );
}
