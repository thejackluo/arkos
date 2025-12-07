# ARK OS Enhanced CLI Guide

## Overview

The ARK OS Enhanced CLI (`ark_repl.py`) provides a rich, interactive terminal interface for chatting with the ARK agent while visualizing memory operations in real-time.

## Features

- **Rich Terminal UI**: Beautiful tables, panels, and formatted output using the Rich library
- **Real-Time Memory Visualization**: See exactly what's happening as memories are stored and retrieved
- **Agent State Tracking**: Monitor agent operations and context
- **Interactive Commands**: Powerful commands for exploring memories and sessions
- **Performance Monitoring**: Track response times, token usage, and session statistics

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Make sure your backend services are running:
   - PostgreSQL/Supabase (default port: 54322)
   - LLM server (default port: 30000)
   - Embedding server (if using separate embeddings)

## Running the CLI

### Basic Usage

```bash
python base_module/ark_repl.py
```

### With Custom User ID

```bash
python base_module/ark_repl.py --user-id my-custom-user
```

### With Custom Configuration

```bash
python base_module/ark_repl.py \
  --user-id alice \
  --db-url "postgresql://user:pass@localhost:5432/db" \
  --llm-url "http://localhost:8000/v1" \
  --state-graph "../state_module/custom_graph.yaml"
```

## Available Commands

### Chat Commands

| Command | Description | Example |
|---------|-------------|---------|
| `<message>` | Send a message to ARK | `Hello, how are you?` |
| `/help` | Show help and available commands | `/help` |
| `/exit` or `/quit` | Exit the CLI | `/exit` |

### Memory Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/search <query>` | Search your memories | `/search favorite color` |
| `/memories` | List recent conversation history | `/memories` |
| `/newsession` | Start a new chat session | `/newsession` |

### Information Commands

| Command | Description | Example |
|---------|-------------|---------|
| `/stats` | Show session statistics | `/stats` |
| `/context` | View agent's current context | `/context` |

## What Happens When You Chat

When you send a message, the CLI shows you exactly what's happening:

1. **Storing in Memory**: Your message is saved to the vector database
2. **Retrieving Relevant Context**: Similar past memories are retrieved
3. **Processing with Agent**: The agent processes your message with context
4. **Response Display**: ARK's response is shown with formatting

## Understanding the Output

### Message Flow Visualization

```
======================================================================
You: What's my favorite color?
======================================================================

1. Storing in Memory...
  ✓ Memory stored successfully

2. Retrieving Relevant Context...
┌────────────────── Retrieved Memories ──────────────────┐
│ # │ Memory                                              │
├───┼─────────────────────────────────────────────────────┤
│ 1 │ user: My favorite color is blue                     │
└───┴─────────────────────────────────────────────────────┘

3. Processing with Agent...
[Agent thinking...]

ARK:
┌────────────────────────────────────────────────────────┐
│ Based on what you've told me before, your favorite     │
│ color is blue!                                         │
└────────────────────────────────────────────────────────┘

Response time: 1.23s
```

## Session Management

### Sessions vs User ID

- **User ID**: Persistent identifier for a user across all sessions
- **Session ID**: Temporary identifier for a single conversation

### Starting a New Session

Use `/newsession` to start fresh while keeping your user history:

```
/newsession

✓ Started new session!
Old session: abc-123-def-456
New session: xyz-789-uvw-012
```

This is useful for:
- Starting a new topic
- Resetting conversation context
- Testing different conversation flows

## Memory Search

The `/search` command uses semantic vector search to find relevant memories:

```
/search machine learning

Searching for: "machine learning"

┌──────────────── Search Results ────────────────┐
│ # │ Memory                                      │
├───┼─────────────────────────────────────────────┤
│ 1 │ user: I'm studying machine learning at MIT  │
│ 2 │ assistant: Machine learning is fascinating  │
│ 3 │ user: Working on a neural network project   │
└───┴─────────────────────────────────────────────┘

Found 3 results
```

## Statistics Tracking

The `/stats` command shows comprehensive session information:

```
/stats

┌─────────────── Statistics ───────────────┐
│ Session Statistics                       │
│                                          │
│ Activity:                                │
│   Messages Sent:       15                │
│   Memories Stored:     30                │
│   Session Duration:    12.5 minutes      │
│                                          │
│ Performance:                             │
│   Avg Response Time:   1.45s             │
│   Total Response Time: 21.75s            │
│                                          │
│ Session Info:                            │
│   User ID:            ark-user-a1b2c3   │
│   Session ID:         sess-xyz123       │
│   Agent ID:           ark-agent-def456  │
│                                          │
│ Agent Context:                           │
│   Messages in Context: 31                │
└──────────────────────────────────────────┘
```

## Tips and Best Practices

### 1. Use Descriptive Messages

The more descriptive your messages, the better the memory system works:

❌ **Bad**: `blue`
✓ **Good**: `My favorite color is blue because it reminds me of the ocean`

### 2. Search Before Asking

Use `/search` to find what ARK already knows:

```
/search favorite
```

### 3. Start New Sessions for New Topics

When switching to a completely different topic:

```
/newsession
```

### 4. Monitor Performance

Use `/stats` to check if response times are getting slow (might indicate context is too large).

### 5. Review Context Periodically

Use `/context` to see what's in the agent's immediate context:

```
/context
```

## Troubleshooting

### "Connection refused" errors

Make sure all backend services are running:

```bash
# Check PostgreSQL
psql -h localhost -p 54322 -U postgres

# Check LLM server
curl http://localhost:30000/v1/models
```

### Slow responses

If responses are slow:

1. Check `/stats` for average response time
2. Consider starting a new session with `/newsession`
3. Reduce the `mem0_limit` in the code if retrieving too many memories

### Memory not being stored

Verify database connection:

```bash
# Check PostgreSQL tables
psql -h localhost -p 54322 -U postgres -d postgres -c "\dt"
```

Should show `conversation_context` and other tables.

## Comparison: Basic vs Enhanced CLI

### Basic CLI (`main_interface.py`)

```
You: Hello
=== Agent Response ===
Hello! How can I help you?
======================
You:
```

### Enhanced CLI (`ark_repl.py`)

```
You: Hello
======================================================================

1. Storing in Memory...
  ✓ Memory stored successfully

2. Retrieving Relevant Context...
  No relevant memories found

3. Processing with Agent...

ARK:
┌────────────────────────────────────────────────────────┐
│ Hello! How can I help you today?                       │
└────────────────────────────────────────────────────────┘

Response time: 0.85s
```

## Architecture

```
┌──────────────┐
│   User Input │
└──────┬───────┘
       │
       v
┌──────────────┐      ┌─────────────┐
│  ArkREPL     │─────>│   Memory    │
│  (UI Layer)  │      │  (Storage)  │
└──────┬───────┘      └─────────────┘
       │
       v
┌──────────────┐      ┌─────────────┐
│    Agent     │─────>│  LLM Link   │
│   (Logic)    │      │  (Model)    │
└──────────────┘      └─────────────┘
```

## Next Steps

- Customize the system prompt in the code
- Add custom commands for your use case
- Integrate with additional tools
- Export conversation history
- Add conversation templates

## Support

For issues or questions:
- Check the main README.md
- Review the source code in `base_module/ark_repl.py`
- Contact the ARK OS team (see contributors in README.md)
