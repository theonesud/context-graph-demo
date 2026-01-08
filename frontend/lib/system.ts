import { createSystem, defaultConfig, defineConfig } from '@chakra-ui/react';

const config = defineConfig({
  theme: {
    tokens: {
      colors: {
        brand: {
          50: { value: '#e6f2ff' },
          100: { value: '#b3d9ff' },
          200: { value: '#80bfff' },
          300: { value: '#4da6ff' },
          400: { value: '#1a8cff' },
          500: { value: '#0073e6' },
          600: { value: '#005cb3' },
          700: { value: '#004480' },
          800: { value: '#002d4d' },
          900: { value: '#00151a' },
        },
        decision: {
          credit: { value: '#38A169' },
          fraud: { value: '#E53E3E' },
          trading: { value: '#3182CE' },
          exception: { value: '#D69E2E' },
          escalation: { value: '#805AD5' },
        },
        node: {
          person: { value: '#4299E1' },
          account: { value: '#48BB78' },
          transaction: { value: '#ED8936' },
          decision: { value: '#9F7AEA' },
          organization: { value: '#F56565' },
          policy: { value: '#38B2AC' },
        },
      },
    },
    semanticTokens: {
      colors: {
        'bg.canvas': {
          value: { _light: '{colors.gray.50}', _dark: '{colors.gray.900}' },
        },
        'bg.surface': {
          value: { _light: 'white', _dark: '{colors.gray.800}' },
        },
        'bg.subtle': {
          value: { _light: '{colors.gray.100}', _dark: '{colors.gray.700}' },
        },
        'border.default': {
          value: { _light: '{colors.gray.200}', _dark: '{colors.gray.600}' },
        },
      },
    },
  },
});

export const system = createSystem(defaultConfig, config);
