# performance/memory-efficiency Specification

## Purpose

Ensures the system can handle very large email volumes (10000+) without exhausting memory, using streaming and batch processing patterns.

## Requirements

### Requirement: Stream-based email processing

The system SHALL process emails in a streaming fashion, loading only one batch at a time into memory, rather than loading all emails at once.

#### Scenario: Process 10000 emails
- **WHEN** scanning 10000 emails
- **THEN** system never holds all 10000 in memory simultaneously

#### Scenario: Memory usage bounded
- **WHEN** processing any number of emails
- **THEN** memory usage grows with batch size, not total email count

### Requirement: Batch database commits

The system SHALL commit emails to the database in batches rather than individual inserts.

#### Scenario: Batch insert
- **WHEN** processing a batch of emails
- **THEN** all emails in batch are inserted in single transaction

#### Scenario: Transaction rollback
- **WHEN** a batch insert fails
- **THEN** entire batch is rolled back, no partial inserts

### Requirement: LRU cache for email bodies

The system SHALL use an LRU (Least Recently Used) cache for email bodies in the TUI, with configurable size.

#### Scenario: Body cache eviction
- **WHEN** cache is full and new body is loaded
- **THEN** least recently viewed body is evicted from cache

#### Scenario: Configurable cache size
- **WHEN** user sets body_cache_size = 100
- **THEN** system caches up to 100 email bodies

### Requirement: Memory usage monitoring

The system SHALL monitor memory usage during large scans and SHALL warn if approaching system limits.

#### Scenario: Memory warning at 80%
- **WHEN** memory usage reaches 80% of available memory
- **THEN** system warns user and suggests reducing batch size

#### Scenario: Memory limit configuration
- **WHEN** user sets memory_limit_mb = 2048
- **THEN** system warns when approaching 2048MB

### Requirement: Efficient data structures

The system SHALL use memory-efficient data structures for storing large numbers of email references.

#### Scenario: Use generators for iteration
- **WHEN** iterating over large email sets
- **THEN** system uses generators to avoid loading all into memory

#### Scenario: Lazy evaluation
- **WHEN** processing requires computation
- **THEN** computation is deferred until needed (lazy evaluation)
