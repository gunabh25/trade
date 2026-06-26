type LogLevel = 'debug' | 'info' | 'warn' | 'error';

type LogContext = Record<string, unknown>;

function serialize(level: LogLevel, message: string, context?: LogContext): string {
  return JSON.stringify({
    level,
    message,
    timestamp: new Date().toISOString(),
    service: 'tradeflow-web',
    ...context,
  });
}

export const logger = {
  debug(message: string, context?: LogContext): void {
    if (process.env.NODE_ENV === 'development') {
      console.debug(serialize('debug', message, context));
    }
  },
  info(message: string, context?: LogContext): void {
    console.info(serialize('info', message, context));
  },
  warn(message: string, context?: LogContext): void {
    console.warn(serialize('warn', message, context));
  },
  error(message: string, context?: LogContext): void {
    console.error(serialize('error', message, context));
  },
};
