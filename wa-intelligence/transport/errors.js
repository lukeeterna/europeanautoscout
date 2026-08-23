'use strict';

class TransportError extends Error {
  constructor(code, message, options = {}) {
    super(message || code);
    this.name = 'TransportError';
    this.code = code || 'TRANSPORT_ERROR';
    this.transient = Boolean(options.transient);
    this.ambiguous = Boolean(options.ambiguous);
    this.statusCode = options.statusCode ?? null;
    this.metaCode = options.metaCode ?? null;
    this.metaType = options.metaType ?? null;
    if (options.cause) this.cause = options.cause;
  }
}

module.exports = { TransportError };
