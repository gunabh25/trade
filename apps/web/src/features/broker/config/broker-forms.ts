export type BrokerFieldType = 'text' | 'password' | 'number' | 'checkbox';

export interface BrokerField {
  key: string;
  label: string;
  type?: BrokerFieldType;
  placeholder?: string;
  defaultValue?: string;
  required?: boolean;
}

export interface BrokerFormConfig {
  id: string;
  label: string;
  description: string;
  fields: BrokerField[];
  buildCredentials: (values: Record<string, string>) => Record<string, unknown>;
}

export const ONBOARDING_BROKERS: BrokerFormConfig[] = [
  {
    id: 'paper',
    label: 'Paper Trading',
    description: 'Simulated account — best for testing copy groups and the dashboard.',
    fields: [
      { key: 'account_name', label: 'Account name', defaultValue: 'Demo Account', required: true },
      {
        key: 'starting_balance',
        label: 'Starting balance (USD)',
        defaultValue: '50000',
        required: true,
      },
      { key: 'account_id', label: 'Account ID', defaultValue: 'paper-1', required: true },
    ],
    buildCredentials: (values) => ({
      account_id: values.account_id ?? 'paper-1',
      account_name: values.account_name ?? 'Demo Account',
      starting_balance: values.starting_balance ?? '50000',
    }),
  },
  {
    id: 'tradovate',
    label: 'Tradovate',
    description: 'Futures broker — use demo credentials for sandbox testing.',
    fields: [
      { key: 'username', label: 'Username', required: true },
      { key: 'password', label: 'Password', type: 'password', required: true },
      { key: 'app_id', label: 'App ID', defaultValue: 'TradeFlow' },
      { key: 'cid', label: 'Client ID (cid)', defaultValue: '0' },
      { key: 'sec', label: 'App secret (sec)', type: 'password' },
      { key: 'demo', label: 'Use demo environment', type: 'checkbox', defaultValue: 'true' },
    ],
    buildCredentials: (values) => ({
      username: values.username,
      password: values.password,
      app_id: values.app_id ?? 'TradeFlow',
      cid: Number(values.cid ?? 0),
      sec: values.sec ?? '',
      demo: values.demo === 'true',
    }),
  },
  {
    id: 'binance',
    label: 'Binance',
    description: 'Spot trading — enable testnet for sandbox keys.',
    fields: [
      { key: 'api_key', label: 'API key', required: true },
      { key: 'api_secret', label: 'API secret', type: 'password', required: true },
      { key: 'testnet', label: 'Use testnet', type: 'checkbox', defaultValue: 'true' },
      { key: 'default_symbol', label: 'Default symbol', defaultValue: 'BTCUSDT' },
    ],
    buildCredentials: (values) => ({
      api_key: values.api_key,
      api_secret: values.api_secret,
      testnet: values.testnet === 'true',
      default_symbol: values.default_symbol ?? 'BTCUSDT',
    }),
  },
];

export function getBrokerFormConfig(brokerId: string): BrokerFormConfig | undefined {
  return ONBOARDING_BROKERS.find((broker) => broker.id === brokerId);
}

export function defaultFieldValues(config: BrokerFormConfig): Record<string, string> {
  return Object.fromEntries(config.fields.map((field) => [field.key, field.defaultValue ?? '']));
}
