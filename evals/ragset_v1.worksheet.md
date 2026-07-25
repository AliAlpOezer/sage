# Hand-labeling worksheet — ragset v1

For each question you want to keep: read the excerpt(s), then **write the
answer in your own words** on its `A[id]:` line. Leave the line blank to
DROP that question (blank = not kept — this blank/filled choice IS your
curation down to 30-50). Excerpts are the ingested chunks for each
source_url; they are reading aids, not answers. For `unanswerable`
questions the correct ground_truth is a refusal, e.g. `Not covered in the corpus.`

When done:  `uv run python -m sage.evals.build_ragset`  → writes ragset_v1.jsonl

Counts: easy=30, hard=28, multi-hop=18, unanswerable=14

## e001 · easy
**Q:** What does create_agent return?
_notes: core API return type_
- **langchain/agents.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Agents
  > An agent is a model calling tools in a loop until a given task is complete.
  > <img src="https://mintcdn.com/langchain-5e9cc07a/jtty0O--UJOKG0nK/oss/images/core_agent_loop.svg?fit=max&auto=format&n=jtty0O--UJOKG0nK&q=85&s=4b4cbb497b6273758a565de1bc90ece0" alt="Core agent loop diagram" style={{height: "300px", width: "auto", justifyContent: "center"}} className="rounded-lg block mx-auto" width="1060" height="760" data-path="oss/images/core_agent_loop.svg" />
  > <Note>
  >   **Agent = Model + Harness**
  > The job of a harness: get the model the right context at the right time for the given task.
  > </Note>
  > A harness is everything around that loop: the model, its prompt, its tools, and any middleware that shapes its
**A[e001]:** it returns an agent object. An instance of the Agent class, that is having .invoke() method

## e002 · easy
**Q:** Which parameters does create_agent accept?
_notes: exact-identifier / params — predicted weak spot_
- **langchain/agents.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Agents
  > An agent is a model calling tools in a loop until a given task is complete.
  > <img src="https://mintcdn.com/langchain-5e9cc07a/jtty0O--UJOKG0nK/oss/images/core_agent_loop.svg?fit=max&auto=format&n=jtty0O--UJOKG0nK&q=85&s=4b4cbb497b6273758a565de1bc90ece0" alt="Core agent loop diagram" style={{height: "300px", width: "auto", justifyContent: "center"}} className="rounded-lg block mx-auto" width="1060" height="760" data-path="oss/images/core_agent_loop.svg" />
  > <Note>
  >   **Agent = Model + Harness**
  > The job of a harness: get the model the right context at the right time for the given task.
  > </Note>
  > A harness is everything around that loop: the model, its prompt, its tools, and any middleware that shapes its
**A[e002]:** model, tools, system_prompt, memory, middleware, checkpointer, store, interrupt_before, interrupt_after, debug

## e003 · easy
**Q:** How do you attach a checkpointer to an agent created with create_agent?
_notes: checkpointer=InMemorySaver() usage_
- **langchain/agents.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Agents
  > An agent is a model calling tools in a loop until a given task is complete.
  > <img src="https://mintcdn.com/langchain-5e9cc07a/jtty0O--UJOKG0nK/oss/images/core_agent_loop.svg?fit=max&auto=format&n=jtty0O--UJOKG0nK&q=85&s=4b4cbb497b6273758a565de1bc90ece0" alt="Core agent loop diagram" style={{height: "300px", width: "auto", justifyContent: "center"}} className="rounded-lg block mx-auto" width="1060" height="760" data-path="oss/images/core_agent_loop.svg" />
  > <Note>
  >   **Agent = Model + Harness**
  > The job of a harness: get the model the right context at the right time for the given task.
  > </Note>
  > A harness is everything around that loop: the model, its prompt, its tools, and any middleware that shapes its
- **langgraph/checkpointers.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Checkpointers
  > > LangGraph checkpointers save graph state as checkpoints at each step, enabling persistence, human-in-the-loop, and fault-tolerant execution.
  > A checkpointer saves a snapshot of graph state at each super-step, organized into **threads**. Compile a graph with a checkpointer to enable human-in-the-loop workflows, time travel debugging, fault-tolerant execution, and conversational memory.
  > <img src="https://mintcdn.com/langchain-5e9cc07a/-_xGPoyjhyiDWTPJ/oss/images/checkpoints.jpg?fit=max&auto=format&n=-_xGPoyjhyiDWTPJ&q=85&s=966566aaae853ed4d240c2d0d067467c" alt="Checkpoints" width="2316" height="748" data-path="oss/images/checkpoints.jpg" />
  > <Info>
  >   **Agent Server handles checkpointing automa
**A[e003]:** with passing a checkpointer argument when calling create_agent, BUT if the thread_id is not assigned in the config data, the agent won't have a persistent memory.

## e004 · easy
**Q:** What is the purpose of the ToolRuntime argument in a tool function?
_notes: ToolRuntime access to state/store_
- **langchain/tools.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Tools
  > Tools extend what [agents](/oss/python/langchain/agents) can do—letting them fetch real-time data, execute code, query external databases, and take actions in the world.
  > Under the hood, tools are callable functions with well-defined inputs and outputs that get passed to a [chat model](/oss/python/langchain/models). The model decides when to invoke a tool based on the conversation context, and what input arguments to provide.
  > <Tip>
  >   For details on how models handle tool calls, see [Tool calling](/oss/python/langchain/models#tool-calling). Trace tool calls and debug errors with [LangSmith](https://smith.langchain.com?utm_source=docs\&utm_medium=cta\&utm_campaign=langsmith-signup\&utm_content=oss-langc
**A[e004]:** The ToolRuntime parameter in a tool function gives the tool direct access to the agent's internal context, memory, and execution utilities without exposing those implementation deatils to the llm. runtime.state accesses the agents current graph state, and runtime.store interacts with the persistent long-term memory store (BaseStore), allowing tools to load or save long-term memories.

## e005 · easy
**Q:** How do you read a value from agent state inside a tool?
_notes: runtime.state.get(...)_
- **langchain/tools.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Tools
  > Tools extend what [agents](/oss/python/langchain/agents) can do—letting them fetch real-time data, execute code, query external databases, and take actions in the world.
  > Under the hood, tools are callable functions with well-defined inputs and outputs that get passed to a [chat model](/oss/python/langchain/models). The model decides when to invoke a tool based on the conversation context, and what input arguments to provide.
  > <Tip>
  >   For details on how models handle tool calls, see [Tool calling](/oss/python/langchain/models#tool-calling). Trace tool calls and debug errors with [LangSmith](https://smith.langchain.com?utm_source=docs\&utm_medium=cta\&utm_campaign=langsmith-signup\&utm_content=oss-langc
**A[e005]:** By using the runtime parameter, the tool can access the state dictionary through runtime.state and read any keys stored there. e.g. in some form like runtime.state["key"]

## e006 · easy
**Q:** What stream_mode value streams LLM tokens as messages?
_notes: stream_mode="messages" — exact value_
- **langchain/streaming.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Streaming
  > > Stream real-time updates from agent runs
  > <Tip>
  >   For new applications, we recommend [event streaming](/oss/python/langchain/event-streaming)—the typed-projection API introduced in LangChain v1.3. Event streaming gives you separate iterators per projection (messages, values, tool calls, subgraphs) so you can consume them independently instead of branching on `stream_mode` chunks.
  > </Tip>
  > LangChain implements a streaming system to surface real-time updates.
  > Streaming is crucial for enhancing the responsiveness of applications built on LLMs. By displaying output progressively, even before a complete response is ready, streaming significantly improves user experience (UX), particularly when dealing
**A[e006]:** The stream_mode value that streams LLM tokens as messages is `"messages"` — setting `stream_mode="messages"` streams LLM tokens with metadata

## e007 · easy
**Q:** How are long-term memories organized in the LangGraph store?
_notes: namespace + key model_
- **concepts/memory.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Memory overview
  > [Memory](/oss/python/langgraph/add-memory) is a system that remembers information about previous interactions. For AI agents, memory is crucial because it lets them remember previous interactions, learn from feedback, and adapt to user preferences. As agents tackle more complex tasks with numerous user interactions, this capability becomes essential for both efficiency and user satisfaction.
  > This conceptual guide covers two types of memory, based on their recall scope:
  > * [Short-term memory](#short-term-memory), or [thread](/oss/python/langgraph/checkpointers#threads)-scoped memory, tracks the ongoing conversation by maintaining message history within a session. LangGraph manages short-term
- **langgraph/stores.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Stores
  > > LangGraph stores provide cross-thread long-term memory, complementing per-thread checkpointer persistence.
  > Stores let agents persist information across threads, including user preferences, accumulated knowledge, and facts that should survive beyond a single conversation. Unlike [checkpointers](/oss/python/langgraph/checkpointers), which save the full graph state scoped to one thread, stores hold arbitrary key-value data accessible from any thread.
  > <img src="https://mintcdn.com/langchain-5e9cc07a/dL5Sn6Cmy9pwtY0V/oss/images/shared_state.png?fit=max&auto=format&n=dL5Sn6Cmy9pwtY0V&q=85&s=354526fb48c5eb11b4b2684a2df40d6c" alt="Model of shared state" width="1482" height="777" data-path="oss/images/shar
**A[e007]:** In LangGraph Store (BaseStore), long-term memories are organized as JSON documents structured around a hierarchical Namespace and Key model.

## e008 · easy
**Q:** What function creates a deep agent?
_notes: create_deep_agent_
- **deepagents/quickstart.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Quickstart
  > > Build your first deep agent in minutes
  > This guide walks you through creating your first deep agent with planning, file system tools, and subagent capabilities. You'll build a research agent that can conduct research and write reports.
  > <Tip>
  >   **Using an AI coding assistant?**
  >   * Install the [LangChain Docs MCP server](/use-these-docs) to give your agent access to up-to-date LangChain documentation and examples.
  >   * Install [LangChain Skills](https://github.com/langchain-ai/langchain-skills) to improve your agent's performance on LangChain ecosystem tasks.
  > </Tip>
  > ## Prerequisites
  > Before you begin, make sure you have an API key from a model provider (e.g., Gemini, Anthropic, OpenAI).
  > <Note>
- **deepagents/overview.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Deep Agents overview
  > > Build agents that can plan, use subagents, and leverage file systems for complex tasks
  > Deep Agents is the easiest way to start building agents and applications that are powered by LLMs—with built-in capabilities for task planning, file systems for context management, subagent-spawning, and long-term memory.
  > You can use deep agents for any task, including complex, multi-step tasks.
  > Deep Agents comes with the following built-in capabilities:
  > * **Take actions in an environment**: Take actions via tools, read and write files, execute code
  > * **Connect to your data**: Load memories, skills, and domain knowledge at the right moment
  > * **Manage growing context**: Summarize history and offloa
**A[e008]:** 

## e009 · easy
**Q:** What is middleware in the LangChain agent framework?
_notes: concept definition_
- **langchain/middleware/overview.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Overview
  > > Control and customize agent execution at every step
  > Middleware provides a way to more tightly control what happens inside the agent. Middleware is useful for the following:
  > * Tracking agent behavior with logging, analytics, and debugging.
  > * Transforming prompts, [tool selection](/oss/python/langchain/middleware/built-in#llm-tool-selector), and output formatting.
  > * Adding [retries](/oss/python/langchain/middleware/built-in#tool-retry), [fallbacks](/oss/python/langchain/middleware/built-in#model-fallback), and early termination logic.
  > * Applying [rate limits](/oss/python/langchain/middleware/built-in#model-call-limit), guardrails, and [PII detection](/oss/python/langchain/middleware/built-in#pii-d
**A[e009]:** 

## e010 · easy
**Q:** How do you install LangChain?
_notes: install command_
- **langchain/install.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Install LangChain
  > To install the LangChain package:
  > <CodeGroup>
  >   ```bash pip theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
  >   pip install -U langchain
  >   # Requires Python 3.10+
  >   ```
  > ```bash uv theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
  >   uv add langchain
  >   # Requires Python 3.10+
  >   ```
  > </CodeGroup>
  > LangChain provides integrations to hundreds of LLMs and thousands of other integrations. These live in independent provider packages.
  > <CodeGroup>
  >   ```bash pip theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
  >   # Installing the OpenAI integration
  >   pip install -U langchain-openai
  > # Installing the Anthropic integration
  >   pip install -U
**A[e010]:** pip install -U langchain

## e011 · easy
**Q:** How do you install LangGraph?
_notes: install command_
- **langgraph/install.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Install LangGraph
  > To install the base LangGraph package:
  > <CodeGroup>
  >   ```bash pip theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
  >   pip install -U langgraph
  >   ```
  >   ```bash uv theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
  >   uv add langgraph
  >   ```
  > </CodeGroup>
  > To use LangGraph you will usually want to access LLMs and define tools.
  > You can do this however you see fit.
  > One way to do this (which we will use in the docs) is to use [LangChain](/oss/python/langchain/overview).
  > Install LangChain with:
  > <CodeGroup>
  >   ```bash pip theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
  >   pip install -U langchain
  >   # Requires Python 3.10+
  >   ```
  >   ```b
**A[e011]:** pip install -U langgraph

## e012 · easy
**Q:** What is a checkpointer used for in LangGraph?
_notes: persistence concept_
- **langgraph/checkpointers.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Checkpointers
  > > LangGraph checkpointers save graph state as checkpoints at each step, enabling persistence, human-in-the-loop, and fault-tolerant execution.
  > A checkpointer saves a snapshot of graph state at each super-step, organized into **threads**. Compile a graph with a checkpointer to enable human-in-the-loop workflows, time travel debugging, fault-tolerant execution, and conversational memory.
  > <img src="https://mintcdn.com/langchain-5e9cc07a/-_xGPoyjhyiDWTPJ/oss/images/checkpoints.jpg?fit=max&auto=format&n=-_xGPoyjhyiDWTPJ&q=85&s=966566aaae853ed4d240c2d0d067467c" alt="Checkpoints" width="2316" height="748" data-path="oss/images/checkpoints.jpg" />
  > <Info>
  >   **Agent Server handles checkpointing automa
- **langgraph/persistence.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Persistence
  > > LangGraph's persistence layer gives agents short-term memory through checkpointers and long-term memory through stores.
  > <a id="checkpoints" />
  > <a id="threads" />
  > <a id="memory-store" />
  > <a id="checkpointer-libraries" />
  > <a id="pending-writes" />
  > <a id="durability-modes" />
  > Persistence lets LangGraph applications keep useful information beyond a single graph run. It matters when an agent needs to continue a conversation, resume after an interruption, recover from a failure, or remember information across interactions.
  > LangGraph provides two complementary persistence systems:
  > * **[Checkpointers](/oss/python/langgraph/checkpointers)** persist a thread's graph state as checkpoints. Use the
**A[e012]:** A checkpointer in LangGraph saves a snapshot of the graph’s state at each super‑step, organized into threads. By storing these checkpoints it enables persistence, human‑in‑the‑loop workflows, time‑travel debugging, fault‑tolerant execution, and conversational memory

## e013 · easy
**Q:** What is an interrupt in LangGraph?
_notes: concept_
- **langgraph/interrupts.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Interrupts
  > Interrupts allow you to pause graph execution at specific points and wait for external input before continuing. This enables human-in-the-loop patterns where you need external input to proceed. When an interrupt is triggered, LangGraph saves the graph state using its [persistence](/oss/python/langgraph/persistence) layer and waits indefinitely until you resume execution.
  > Interrupts work by calling the `interrupt()` function at any point in your graph nodes. The function accepts any JSON-serializable value which is surfaced to the caller. When you're ready to continue, you resume execution by re-invoking the graph using `Command`, which then becomes the return value of the `interrupt()` call from
**A[e013]:** In LangGraph, an interrupt is a mechanism that pauses the execution of a graph at a specific point and yields control back to the caller (such as a user interface or human-in-the-loop workflow).

## e014 · easy
**Q:** What does the InMemorySaver checkpointer do?
_notes: exact-identifier_
- **langgraph/checkpointers.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Checkpointers
  > > LangGraph checkpointers save graph state as checkpoints at each step, enabling persistence, human-in-the-loop, and fault-tolerant execution.
  > A checkpointer saves a snapshot of graph state at each super-step, organized into **threads**. Compile a graph with a checkpointer to enable human-in-the-loop workflows, time travel debugging, fault-tolerant execution, and conversational memory.
  > <img src="https://mintcdn.com/langchain-5e9cc07a/-_xGPoyjhyiDWTPJ/oss/images/checkpoints.jpg?fit=max&auto=format&n=-_xGPoyjhyiDWTPJ&q=85&s=966566aaae853ed4d240c2d0d067467c" alt="Checkpoints" width="2316" height="748" data-path="oss/images/checkpoints.jpg" />
  > <Info>
  >   **Agent Server handles checkpointing automa
**A[e014]:** In LangGraph, the InMemorySaver is a lightweight, non-persistent checkpointer that stores thread state snapshots directly in your application's RAM (in-memory data structures like Python dictionaries).

## e015 · easy
**Q:** What is a subagent in the multi-agent framework?
_notes: concept_
- **langchain/multi-agent/subagents.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Subagents
  > In the **subagents** architecture, a central main [agent](/oss/python/langchain/agents) (often referred to as a **supervisor**) coordinates subagents by calling them as [tools](/oss/python/langchain/tools). The main agent decides which subagent to invoke, what input to provide, and how to combine results. Subagents are stateless—they don't remember past interactions, with all conversation memory maintained by the main agent. This provides [context](/oss/python/langchain/context-engineering) isolation: each subagent invocation works in a clean context window, preventing context bloat in the main conversation.
  > For built-in subagent support, see [Deep Agents](/oss/python/deepagents/subagents).
  > ```me
**A[e015]:** A subagent is a stateless component that the main (supervisor) agent invokes as a tool to perform specialized work in an isolated context, returning only the final result so the main agent’s conversation stays clean and avoids context bloat

## e016 · easy
**Q:** What is a handoff between agents?
_notes: concept_
- **langchain/multi-agent/handoffs.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Handoffs
  > In the **handoffs** architecture, behavior changes dynamically based on state. The core mechanism: [tools](/oss/python/langchain/tools) update a state variable (e.g., `current_step` or `active_agent`) that persists across turns, and the system reads this variable to adjust behavior—either applying different configuration (system prompt, tools) or routing to a different [agent](/oss/python/langchain/agents). This pattern supports both handoffs between distinct agents and dynamic configuration changes within a single agent.
  > <Tip>
  >   The term **handoffs** was coined by [OpenAI](https://openai.github.io/openai-agents-python/handoffs/) for using tool calls (e.g., `transfer_to_sales_agent`) to transfer co
**A[e016]:** 

## e017 · easy
**Q:** What is the difference between short-term and long-term memory in LangChain?
_notes: concept contrast (single topic pair)_
- **langchain/short-term-memory.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Short-term memory
  > ## Overview
  > Memory is a system that remembers information about previous interactions. For AI agents, memory is crucial because it lets them remember previous interactions, learn from feedback, and adapt to user preferences. As agents tackle more complex tasks with numerous user interactions, this capability becomes essential for both efficiency and user satisfaction.
  > Short term memory lets your application remember previous interactions within a single thread or conversation.
  > <Note>
  >   A thread organizes multiple interactions in a session, similar to the way email groups messages in a single conversation.
  > </Note>
  > Conversation history is the most common form of short-term memory. Long con
- **langchain/long-term-memory.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Long-term memory
  > > Add long-term memory to LangChain agents to store and recall data across conversations and sessions
  > Long-term memory lets your agent store and recall information across different conversations and sessions.
  > Unlike [short-term memory](/oss/python/langchain/short-term-memory), which is scoped to a single thread, long-term memory persists across threads and can be recalled at any time.
  > Long-term memory is built on [LangGraph stores](/oss/python/langgraph/stores), which save data as JSON documents organized by namespace and key.
  > ## Usage
  > To add long-term memory to an agent, create a store and pass it to [`create_agent`](https://reference.langchain.com/python/langchain/agents/factory/create_
**A[e017]:** 

## e018 · easy
**Q:** How do you define structured output for an agent?
_notes: structured output_
- **langchain/structured-output.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Structured output
  > Structured output allows agents to return data in a specific, predictable format. Instead of parsing natural language responses, you get structured data in the form of JSON objects, [Pydantic models](https://docs.pydantic.dev/latest/concepts/models/#basic-model-usage), or dataclasses that your application can use directly.
  > <Tip>
  >   This page covers structured output with agents using `create_agent`. To use structured output directly on a model (outside of agents), see [Models - Structured output](/oss/python/langchain/models#structured-output).
  > </Tip>
  > LangChain's [`create_agent`](https://reference.langchain.com/python/langchain/agents/factory/create_agent) handles structured output automat
**A[e018]:** 

## e019 · easy
**Q:** What is the Model Context Protocol (MCP) in LangChain?
_notes: concept_
- **langchain/mcp.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Model Context Protocol (MCP)
  > [Model Context Protocol (MCP)](https://modelcontextprotocol.io/introduction) is an open protocol that standardizes how applications provide tools and context to LLMs. LangChain agents can use tools defined on MCP servers using the [`langchain-mcp-adapters`](https://github.com/langchain-ai/langchain-mcp-adapters) library.
  > ## Quickstart
  > Install the `langchain-mcp-adapters` library:
  > <CodeGroup>
  >   ```bash pip theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
  >   pip install langchain-mcp-adapters
  >   ```
  > ```bash uv theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
  >   uv add langchain-mcp-adapters
  >   ```
  > </CodeGroup>
  > `langchain-mcp-adapters` ena
**A[e019]:** 

## e020 · easy
**Q:** What are guardrails used for in LangChain agents?
_notes: concept_
- **langchain/guardrails.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Guardrails
  > > Implement safety checks and content filtering for your agents
  > Guardrails help you build safe, compliant AI applications by validating and filtering content at key points in your agent's execution. They can detect sensitive information, enforce content policies, validate outputs, and prevent unsafe behaviors before they cause problems.
  > Common use cases include:
  > * Preventing PII leakage
  > * Detecting and blocking prompt injection attacks
  > * Blocking inappropriate or harmful content
  > * Enforcing business rules and compliance requirements
  > * Validating output quality and accuracy
  > You can implement guardrails using [middleware](/oss/python/langchain/middleware) to intercept execution at strategic poin
**A[e020]:** 

## e021 · easy
**Q:** How do you enable human-in-the-loop in an agent?
_notes: HITL_
- **langchain/human-in-the-loop.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Human-in-the-loop
  > The Human-in-the-Loop (HITL) [middleware](/oss/python/langchain/middleware/built-in#human-in-the-loop) lets you add human oversight to agent tool calls.
  > When a model proposes an action that might require review—for example, writing to a file or executing SQL—the middleware can pause execution and wait for a decision.
  > It does this by checking each tool call against a configurable policy. If intervention is needed, the middleware issues an [interrupt](https://reference.langchain.com/python/langgraph/types/interrupt) that halts execution. The graph state is saved using LangGraph's [persistence layer](/oss/python/langgraph/persistence), so execution can pause safely and resume later.
  > A human
**A[e021]:** fetch HumanInTheLoopMiddleware first than set a middleware and checkpointer, so the state snapshot gets saved. Than interrupter and its wanted behaviour. And the thread_id, so the agent can have a persistent memory.

## e022 · easy
**Q:** What is a Command object used for in a handoff tool?
_notes: exact-identifier Command_
- **langchain/multi-agent/handoffs.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Handoffs
  > In the **handoffs** architecture, behavior changes dynamically based on state. The core mechanism: [tools](/oss/python/langchain/tools) update a state variable (e.g., `current_step` or `active_agent`) that persists across turns, and the system reads this variable to adjust behavior—either applying different configuration (system prompt, tools) or routing to a different [agent](/oss/python/langchain/agents). This pattern supports both handoffs between distinct agents and dynamic configuration changes within a single agent.
  > <Tip>
  >   The term **handoffs** was coined by [OpenAI](https://openai.github.io/openai-agents-python/handoffs/) for using tool calls (e.g., `transfer_to_sales_agent`) to transfer co
**A[e022]:** 

## e023 · easy
**Q:** What does the LangGraph Functional API provide?
_notes: concept_
- **langgraph/functional-api.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Functional API overview
  > The **Functional API** allows you to add LangGraph's key features ([persistence](/oss/python/langgraph/persistence), [memory](/oss/python/langgraph/add-memory), [human-in-the-loop](/oss/python/langgraph/interrupts), and [streaming](/oss/python/langgraph/streaming)) to your applications with minimal changes to your existing code.
  > It is designed to integrate these features into existing code that may use standard language primitives for branching and control flow, such as `if` statements, `for` loops, and function calls. Unlike many data orchestration frameworks that require restructuring code into an explicit pipeline or DAG, the Functional API allows you to incorporate these capabili
**A[e023]:** 

## e024 · easy
**Q:** What is time travel in LangGraph?
_notes: concept_
- **langgraph/use-time-travel.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Use time-travel
  > > Replay past executions and fork to explore alternative paths in LangGraph
  > ## Overview
  > LangGraph supports time travel through [checkpoints](/oss/python/langgraph/checkpointers#checkpoints):
  > * **[Replay](#replay)**: Retry from a prior checkpoint.
  > * **[Fork](#fork)**: Branch from a prior checkpoint with modified state to explore an alternative path.
  > Both work by resuming from a prior checkpoint. Nodes before the checkpoint are not re-executed (results are already saved). Nodes after the checkpoint re-execute, including any LLM calls, API requests, and [interrupts](/oss/python/langgraph/interrupts) (which may produce different results).
  > ## Replay
  > Invoke the graph with a prior checkpoint's c
**A[e024]:** ability to inspect, pause, rewind, edit and fork the execution history of the graph - realized by resuming from any checkpoint, a saved snapshpt of an agents state at a given moment.

## e025 · easy
**Q:** What is a StateSnapshot in LangGraph?
_notes: exact-identifier_
- **langgraph/persistence.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Persistence
  > > LangGraph's persistence layer gives agents short-term memory through checkpointers and long-term memory through stores.
  > <a id="checkpoints" />
  > <a id="threads" />
  > <a id="memory-store" />
  > <a id="checkpointer-libraries" />
  > <a id="pending-writes" />
  > <a id="durability-modes" />
  > Persistence lets LangGraph applications keep useful information beyond a single graph run. It matters when an agent needs to continue a conversation, resume after an interruption, recover from a failure, or remember information across interactions.
  > LangGraph provides two complementary persistence systems:
  > * **[Checkpointers](/oss/python/langgraph/checkpointers)** persist a thread's graph state as checkpoints. Use the
**A[e025]:** 

## e026 · easy
**Q:** How do you retrieve stored memories by semantic search in LangGraph?
_notes: store.asearch_
- **langgraph/add-memory.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Memory
  > AI applications need [memory](/oss/python/concepts/memory) to share context across multiple interactions. In LangGraph, you can add two types of memory:
  > * [Add short-term memory](#add-short-term-memory) as a part of your agent's [state](/oss/python/langgraph/graph-api#state) to enable multi-turn conversations.
  > * [Add long-term memory](#add-long-term-memory) to store user-specific or application-level data across sessions.
  > ## Add short-term memory
  > **Short-term** memory (thread-level [persistence](/oss/python/langgraph/persistence)) enables agents to track multi-turn conversations. To add short-term memory:
  > ```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
  > from langgrap
- **langgraph/stores.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Stores
  > > LangGraph stores provide cross-thread long-term memory, complementing per-thread checkpointer persistence.
  > Stores let agents persist information across threads, including user preferences, accumulated knowledge, and facts that should survive beyond a single conversation. Unlike [checkpointers](/oss/python/langgraph/checkpointers), which save the full graph state scoped to one thread, stores hold arbitrary key-value data accessible from any thread.
  > <img src="https://mintcdn.com/langchain-5e9cc07a/dL5Sn6Cmy9pwtY0V/oss/images/shared_state.png?fit=max&auto=format&n=dL5Sn6Cmy9pwtY0V&q=85&s=354526fb48c5eb11b4b2684a2df40d6c" alt="Model of shared state" width="1482" height="777" data-path="oss/images/shar
**A[e026]:** 

## e027 · easy
**Q:** What is the Graph API in LangGraph?
_notes: concept_
- **langgraph/graph-api.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Graph API overview
  > ## Graphs
  > At its core, LangGraph models agent workflows as graphs. You define the behavior of your agents using three key components:
  > 1. [`State`](#state): A shared data structure that represents the current snapshot of your application. It can be any data type, but is typically defined using a shared state schema.
  > 2. [`Nodes`](#nodes): Functions that encode the logic of your agents. They receive the current state as input, perform some computation or side-effect, and return an updated state.
  > 3. [`Edges`](#edges): Functions that determine which `Node` to execute next based on the current state. They can be conditional branches or fixed transitions.
  > By composing `Nodes` and `Edges`, you
**A[e027]:** Graph Api in Langgraph is the foundational framwork used to build stateful, multi-step ai applications and agentic workflows as directed graphs. It has 4 core buillding blocks: State Schema: the sate  is a shared data structure, every node reads from this state and returns upgrades to it. Nodes: are python functions that execute logic. such as prompting an LLM, executing Python code, querying a vector DB, or calling an API. They can accept current graph state as input and a dictionary containing updated key-value pairs to write back to state as output. Edge: defines the execution oaths between nodes

## e028 · easy
**Q:** What does the guardrails page recommend for input validation?
_notes: concept_
- **langchain/guardrails.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Guardrails
  > > Implement safety checks and content filtering for your agents
  > Guardrails help you build safe, compliant AI applications by validating and filtering content at key points in your agent's execution. They can detect sensitive information, enforce content policies, validate outputs, and prevent unsafe behaviors before they cause problems.
  > Common use cases include:
  > * Preventing PII leakage
  > * Detecting and blocking prompt injection attacks
  > * Blocking inappropriate or harmful content
  > * Enforcing business rules and compliance requirements
  > * Validating output quality and accuracy
  > You can implement guardrails using [middleware](/oss/python/langchain/middleware) to intercept execution at strategic poin
**A[e028]:** 

## e029 · easy
**Q:** What is a Store (BaseStore) in LangChain?
_notes: exact-identifier BaseStore_
- **langgraph/stores.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Stores
  > > LangGraph stores provide cross-thread long-term memory, complementing per-thread checkpointer persistence.
  > Stores let agents persist information across threads, including user preferences, accumulated knowledge, and facts that should survive beyond a single conversation. Unlike [checkpointers](/oss/python/langgraph/checkpointers), which save the full graph state scoped to one thread, stores hold arbitrary key-value data accessible from any thread.
  > <img src="https://mintcdn.com/langchain-5e9cc07a/dL5Sn6Cmy9pwtY0V/oss/images/shared_state.png?fit=max&auto=format&n=dL5Sn6Cmy9pwtY0V&q=85&s=354526fb48c5eb11b4b2684a2df40d6c" alt="Model of shared state" width="1482" height="777" data-path="oss/images/shar
- **langchain/tools.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Tools
  > Tools extend what [agents](/oss/python/langchain/agents) can do—letting them fetch real-time data, execute code, query external databases, and take actions in the world.
  > Under the hood, tools are callable functions with well-defined inputs and outputs that get passed to a [chat model](/oss/python/langchain/models). The model decides when to invoke a tool based on the conversation context, and what input arguments to provide.
  > <Tip>
  >   For details on how models handle tool calls, see [Tool calling](/oss/python/langchain/models#tool-calling). Trace tool calls and debug errors with [LangSmith](https://smith.langchain.com?utm_source=docs\&utm_medium=cta\&utm_campaign=langsmith-signup\&utm_content=oss-langc
**A[e029]:** 

## e030 · easy
**Q:** What is the Runtime object in a LangChain agent?
_notes: concept_
- **langchain/runtime.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Runtime
  > ## Overview
  > LangChain's [`create_agent`](https://reference.langchain.com/python/langchain/agents/factory/create_agent) runs on LangGraph's runtime under the hood.
  > LangGraph exposes a [`Runtime`](https://reference.langchain.com/python/langgraph/runtime/Runtime) object with the following information:
  > 1. **Context**: static information like user id, db connections, or other dependencies for an agent invocation
  > 2. **Store**: a [BaseStore](https://reference.langchain.com/python/langchain-core/stores/BaseStore) instance used for [long-term memory](/oss/python/langchain/long-term-memory)
  > 3. **Stream writer**: an object used for streaming information via the `"custom"` stream mode
  > 4. **Execution info**: id
**A[e030]:** In LangChain and LangGraph, the Runtime object serves as a dependency injection mechanism. Instead of using hardcoded global state or polluting the agent's LLM context with non-model dependencies, the Runtime object provides tools, middleware, and graph nodes with direct access to static context, long-term memory, and execution metadata.

## h001 · hard
**Q:** In create_agent, what is the difference between passing a model as a string like 'anthropic:claude-sonnet-4-6' versus a model instance?
_notes: exact-identifier + nuance_
- **langchain/agents.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Agents
  > An agent is a model calling tools in a loop until a given task is complete.
  > <img src="https://mintcdn.com/langchain-5e9cc07a/jtty0O--UJOKG0nK/oss/images/core_agent_loop.svg?fit=max&auto=format&n=jtty0O--UJOKG0nK&q=85&s=4b4cbb497b6273758a565de1bc90ece0" alt="Core agent loop diagram" style={{height: "300px", width: "auto", justifyContent: "center"}} className="rounded-lg block mx-auto" width="1060" height="760" data-path="oss/images/core_agent_loop.svg" />
  > <Note>
  >   **Agent = Model + Harness**
  > The job of a harness: get the model the right context at the right time for the given task.
  > </Note>
  > A harness is everything around that loop: the model, its prompt, its tools, and any middleware that shapes its
- **langchain/models.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Models
  > [LLMs](https://en.wikipedia.org/wiki/Large_language_model) are powerful AI tools that can interpret and generate text like humans. They're versatile enough to write content, translate languages, summarize, and answer questions without needing specialized training for each task.
  > In addition to text generation, many models support:
  > * <Icon icon="hammer" size={16} /> [Tool calling](#tool-calling) - calling external tools (like databases queries or API calls) and use results in their responses.
  > * <Icon icon="layout-grid" size={16} /> [Structured output](#structured-output) - where the model's response is constrained to follow a defined format.
  > * <Icon icon="photo" size={16} /> [Multimodality](#multimoda
**A[h001]:** 

## h002 · hard
**Q:** What is the difference between passing checkpointer=True and checkpointer=InMemorySaver() to create_agent?
_notes: subtle behavior — predicted weak spot_
- **langgraph/use-subgraphs.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Subgraphs
  > This guide explains the mechanics of using subgraphs. A subgraph is a [graph](/oss/python/langgraph/graph-api#graphs) that is used as a [node](/oss/python/langgraph/graph-api#nodes) in another graph.
  > Subgraphs are useful for:
  > * Building [multi-agent systems](/oss/python/langchain/multi-agent)
  > * Reusing a set of nodes in multiple graphs
  > * Distributing development: when you want different teams to work on different parts of the graph independently, you can define each part as a subgraph, and as long as the subgraph interface (the input and output schemas) is respected, the parent graph can be built without knowing any details of the subgraph
  > ## Setup
  > <CodeGroup>
  >   ```bash pip theme={"theme":{"ligh
- **langgraph/checkpointers.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Checkpointers
  > > LangGraph checkpointers save graph state as checkpoints at each step, enabling persistence, human-in-the-loop, and fault-tolerant execution.
  > A checkpointer saves a snapshot of graph state at each super-step, organized into **threads**. Compile a graph with a checkpointer to enable human-in-the-loop workflows, time travel debugging, fault-tolerant execution, and conversational memory.
  > <img src="https://mintcdn.com/langchain-5e9cc07a/-_xGPoyjhyiDWTPJ/oss/images/checkpoints.jpg?fit=max&auto=format&n=-_xGPoyjhyiDWTPJ&q=85&s=966566aaae853ed4d240c2d0d067467c" alt="Checkpoints" width="2316" height="748" data-path="oss/images/checkpoints.jpg" />
  > <Info>
  >   **Agent Server handles checkpointing automa
**A[h002]:** The corpus doesn't document `checkpointer=True`, only explicit checkpointer instances such as `InMemorySaver` or a durable checkpointer passed at compile time.

## h003 · hard
**Q:** How do you write a class-based custom middleware with both sync and async hooks?
_notes: AgentMiddleware class hooks_
- **langchain/middleware/custom.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Custom middleware
  > Build custom middleware by implementing hooks that run at specific points in the agent execution flow.
  > ## Hooks
  > Middleware provides two styles of hooks to intercept agent execution:
  > <CardGroup cols={2}>
  >   <Card title="Node-style hooks" icon="share" href="#node-style-hooks">
  >     Run sequentially at specific execution points.
  >   </Card>
  >   <Card title="Wrap-style hooks" icon="container" href="#wrap-style-hooks">
  >     Run around each model or tool call.
  >   </Card>
  > </CardGroup>
  > ### Node-style hooks
  > Run sequentially at specific execution points. Use for logging, validation, and state updates.
  > Choose the hooks your middleware needs. You can choose between node-style hooks and wrap-style hooks.
**A[h003]:** 

## h004 · hard
**Q:** What is wrap_tool_call and when would you use it?
_notes: exact-identifier wrap_tool_call_
- **langchain/middleware/custom.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Custom middleware
  > Build custom middleware by implementing hooks that run at specific points in the agent execution flow.
  > ## Hooks
  > Middleware provides two styles of hooks to intercept agent execution:
  > <CardGroup cols={2}>
  >   <Card title="Node-style hooks" icon="share" href="#node-style-hooks">
  >     Run sequentially at specific execution points.
  >   </Card>
  >   <Card title="Wrap-style hooks" icon="container" href="#wrap-style-hooks">
  >     Run around each model or tool call.
  >   </Card>
  > </CardGroup>
  > ### Node-style hooks
  > Run sequentially at specific execution points. Use for logging, validation, and state updates.
  > Choose the hooks your middleware needs. You can choose between node-style hooks and wrap-style hooks.
**A[h004]:** 

## h005 · hard
**Q:** How do you stream both partial JSON tool-call args and the completed parsed tool calls?
_notes: streaming tool calls nuance_
- **langchain/streaming.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Streaming
  > > Stream real-time updates from agent runs
  > <Tip>
  >   For new applications, we recommend [event streaming](/oss/python/langchain/event-streaming)—the typed-projection API introduced in LangChain v1.3. Event streaming gives you separate iterators per projection (messages, values, tool calls, subgraphs) so you can consume them independently instead of branching on `stream_mode` chunks.
  > </Tip>
  > LangChain implements a streaming system to surface real-time updates.
  > Streaming is crucial for enhancing the responsiveness of applications built on LLMs. By displaying output progressively, even before a complete response is ready, streaming significantly improves user experience (UX), particularly when dealing
**A[h005]:** 

## h006 · hard
**Q:** What is the state_schema on AgentMiddleware for, and how does it extend agent state?
_notes: exact-identifier state_schema_
- **langchain/middleware/custom.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Custom middleware
  > Build custom middleware by implementing hooks that run at specific points in the agent execution flow.
  > ## Hooks
  > Middleware provides two styles of hooks to intercept agent execution:
  > <CardGroup cols={2}>
  >   <Card title="Node-style hooks" icon="share" href="#node-style-hooks">
  >     Run sequentially at specific execution points.
  >   </Card>
  >   <Card title="Wrap-style hooks" icon="container" href="#wrap-style-hooks">
  >     Run around each model or tool call.
  >   </Card>
  > </CardGroup>
  > ### Node-style hooks
  > Run sequentially at specific execution points. Use for logging, validation, and state updates.
  > Choose the hooks your middleware needs. You can choose between node-style hooks and wrap-style hooks.
- **migrate/langchain-v1.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # LangChain v1 migration guide
  > This guide outlines the major changes between [LangChain v1](/oss/python/releases/langchain-v1) and previous versions.
  > ### `langchain-classic`
  > If you were using any of the following from the `langchain` package, you'll need to install [`langchain-classic`](https://pypi.org/project/langchain-classic/) and update your imports:
  > * Legacy chains (`LLMChain`, `ConversationChain`, etc.)
  > * Retrievers (e.g. `MultiQueryRetriever` or anything from the previous `langchain.retrievers` module)
  > * The indexing API
  > * The hub module (for managing prompts programmatically)
  > * Embeddings modules (e.g. `CacheBackedEmbeddings` and community embeddings)
  > * [`langchain-community`](https://pypi.org/proje
**A[h006]:** 

## h007 · hard
**Q:** How does a stateless router differ from wrapping the router as a tool for a conversational agent?
_notes: design nuance_
- **langchain/multi-agent/router.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Router
  > In the **router** architecture, a routing step classifies input and directs it to specialized [agents](/oss/python/langchain/agents). This is useful when you have distinct **verticals** (separate knowledge domains that each require their own agent).
  > ```mermaid theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
  > graph LR
  >     A([Query]) --> B[Router]
  >     B --> C[Agent A]
  >     B --> D[Agent B]
  >     B --> E[Agent C]
  >     C --> F[Synthesize]
  >     D --> F
  >     E --> F
  >     F --> G([Combined answer])
  >     classDef trigger fill:#F6FFDB,stroke:#6E8900,stroke-width:2px,color:#2E3900
  >     classDef process fill:#E5F4FF,stroke:#006DDD,stroke-width:2px,color:#030710
  >     class A,G trigger
  >     class B,C
**A[h007]:** 

## h008 · hard
**Q:** How do you pass a context_schema to create_agent and access it at runtime?
_notes: exact-identifier context_schema_
- **langchain/agents.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Agents
  > An agent is a model calling tools in a loop until a given task is complete.
  > <img src="https://mintcdn.com/langchain-5e9cc07a/jtty0O--UJOKG0nK/oss/images/core_agent_loop.svg?fit=max&auto=format&n=jtty0O--UJOKG0nK&q=85&s=4b4cbb497b6273758a565de1bc90ece0" alt="Core agent loop diagram" style={{height: "300px", width: "auto", justifyContent: "center"}} className="rounded-lg block mx-auto" width="1060" height="760" data-path="oss/images/core_agent_loop.svg" />
  > <Note>
  >   **Agent = Model + Harness**
  > The job of a harness: get the model the right context at the right time for the given task.
  > </Note>
  > A harness is everything around that loop: the model, its prompt, its tools, and any middleware that shapes its
- **langchain/context-engineering.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Context engineering in agents
  > ## Overview
  > The hard part of building agents (or any LLM application) is making them reliable enough. While they may work for a prototype, they often fail in real-world use cases.
  > ### Why do agents fail?
  > When agents fail, it's usually because the LLM call inside the agent took the wrong action / didn't do what we expected. LLMs fail for one of two reasons:
  > 1. The underlying LLM is not capable enough
  > 2. The "right" context was not passed to the LLM
  > More often than not - it's actually the second reason that causes agents to not be reliable.
  > **Context engineering** is providing the right information and tools in the right format so the LLM can accomplish a task. This is the num
**A[h008]:** 

## h009 · hard
**Q:** What are the built-in (prebuilt) middleware options and what does each do?
_notes: enumeration — precision test_
- **langchain/middleware/built-in.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Prebuilt middleware
  > > Prebuilt middleware for common agent use cases
  > LangChain and [Deep Agents](/oss/python/deepagents/overview) provide prebuilt middleware for common use cases. Each middleware is production-ready and configurable for your specific needs.
  > ## Provider-agnostic middleware
  > The following middleware work with any LLM provider:
  > | Middleware                                    | Description                                                                                   |
  > | --------------------------------------------- | --------------------------------------------------------------------------------------------- |
  > | [Summarization](#summarization)               | Automatically summarize conver
**A[h009]:** 

## h010 · hard
**Q:** How do you configure a StoreBackend for a deep agent with an InMemoryStore?
_notes: exact-identifier StoreBackend_
- **deepagents/customization.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Customize Deep Agents
  > > Learn how to customize Deep Agents with system prompts, tools, subagents, and more
  > Build the harness around your goal. `create_deep_agent` gives you a production-ready foundation: connect it to your data, shape its behavior, and add the capabilities your use case needs.
  > <CodeGroup>
  >   ```python Google theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
  >   from deepagents import create_deep_agent
  > agent = create_deep_agent(
  >       model="google_genai:gemini-3.5-flash",
  >       system_prompt="You are a helpful assistant.",
  >       tools=[search, fetch_url],
  >       memory=["./AGENTS.md"],
  >       skills=["./skills/"],
  >   )
  >   ```
  > ```python OpenAI theme={"theme":{"light":"catppu
- **deepagents/backends.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Backends
  > > Choose and configure filesystem backends for Deep Agents. You can specify routes to different backends, implement virtual filesystems, and enforce policies.
  > Deep Agents expose a filesystem surface to the agent via tools like `ls`, `read_file`, `write_file`, `edit_file`, `glob`, and `grep`. These tools operate through a pluggable backend. The `read_file` tool natively supports image files (`.png`, `.jpg`, `.jpeg`, `.gif`, `.webp`) across all backends, returning them as multimodal content blocks.
  > Sandboxes and the [`LocalShellBackend`](https://reference.langchain.com/python/deepagents/backends/local_shell/LocalShellBackend) also provide an `execute` tool.
  > This page explains how to:
  > * [Choose a ba
**A[h010]:** 

## h011 · hard
**Q:** What is the difference between the Graph API and the Functional API, and when should you choose each?
_notes: decision guidance_
- **langgraph/choosing-apis.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Choosing between Graph and Functional APIs
  > LangGraph provides two different APIs to build agent workflows: the **Graph API** and the **Functional API**. Both APIs share the same underlying runtime and can be used together in the same application, but they are designed for different use cases and development preferences.
  > This guide will help you understand when to use each API based on your specific requirements.
  > ## Quick decision guide
  > Use the **Graph API** when you need:
  > * **Complex workflow visualization** for debugging and documentation
  > * **Explicit state management** with shared data across multiple nodes
  > * **Conditional branching** with multiple decision points
  > * **Parallel execution paths** that nee
**A[h011]:** 

## h012 · hard
**Q:** How do PregelTask and interrupts appear in a StateSnapshot when a graph is paused?
_notes: exact-identifier PregelTask_
- **langgraph/checkpointers.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Checkpointers
  > > LangGraph checkpointers save graph state as checkpoints at each step, enabling persistence, human-in-the-loop, and fault-tolerant execution.
  > A checkpointer saves a snapshot of graph state at each super-step, organized into **threads**. Compile a graph with a checkpointer to enable human-in-the-loop workflows, time travel debugging, fault-tolerant execution, and conversational memory.
  > <img src="https://mintcdn.com/langchain-5e9cc07a/-_xGPoyjhyiDWTPJ/oss/images/checkpoints.jpg?fit=max&auto=format&n=-_xGPoyjhyiDWTPJ&q=85&s=966566aaae853ed4d240c2d0d067467c" alt="Checkpoints" width="2316" height="748" data-path="oss/images/checkpoints.jpg" />
  > <Info>
  >   **Agent Server handles checkpointing automa
- **langgraph/interrupts.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Interrupts
  > Interrupts allow you to pause graph execution at specific points and wait for external input before continuing. This enables human-in-the-loop patterns where you need external input to proceed. When an interrupt is triggered, LangGraph saves the graph state using its [persistence](/oss/python/langgraph/persistence) layer and waits indefinitely until you resume execution.
  > Interrupts work by calling the `interrupt()` function at any point in your graph nodes. The function accepts any JSON-serializable value which is surfaced to the caller. When you're ready to continue, you resume execution by re-invoking the graph using `Command`, which then becomes the return value of the `interrupt()` call from
**A[h012]:** 

## h013 · hard
**Q:** How do you namespace long-term memories per user, and why include user or org IDs in the namespace?
_notes: namespace design_
- **langchain/long-term-memory.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Long-term memory
  > > Add long-term memory to LangChain agents to store and recall data across conversations and sessions
  > Long-term memory lets your agent store and recall information across different conversations and sessions.
  > Unlike [short-term memory](/oss/python/langchain/short-term-memory), which is scoped to a single thread, long-term memory persists across threads and can be recalled at any time.
  > Long-term memory is built on [LangGraph stores](/oss/python/langgraph/stores), which save data as JSON documents organized by namespace and key.
  > ## Usage
  > To add long-term memory to an agent, create a store and pass it to [`create_agent`](https://reference.langchain.com/python/langchain/agents/factory/create_
- **concepts/memory.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Memory overview
  > [Memory](/oss/python/langgraph/add-memory) is a system that remembers information about previous interactions. For AI agents, memory is crucial because it lets them remember previous interactions, learn from feedback, and adapt to user preferences. As agents tackle more complex tasks with numerous user interactions, this capability becomes essential for both efficiency and user satisfaction.
  > This conceptual guide covers two types of memory, based on their recall scope:
  > * [Short-term memory](#short-term-memory), or [thread](/oss/python/langgraph/checkpointers#threads)-scoped memory, tracks the ongoing conversation by maintaining message history within a session. LangGraph manages short-term
**A[h013]:** 

## h014 · hard
**Q:** What changed about how models are configured in the LangChain v1 migration (pre-bound models)?
_notes: migration nuance_
- **migrate/langchain-v1.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # LangChain v1 migration guide
  > This guide outlines the major changes between [LangChain v1](/oss/python/releases/langchain-v1) and previous versions.
  > ### `langchain-classic`
  > If you were using any of the following from the `langchain` package, you'll need to install [`langchain-classic`](https://pypi.org/project/langchain-classic/) and update your imports:
  > * Legacy chains (`LLMChain`, `ConversationChain`, etc.)
  > * Retrievers (e.g. `MultiQueryRetriever` or anything from the previous `langchain.retrievers` module)
  > * The indexing API
  > * The hub module (for managing prompts programmatically)
  > * Embeddings modules (e.g. `CacheBackedEmbeddings` and community embeddings)
  > * [`langchain-community`](https://pypi.org/proje
**A[h014]:** 

## h015 · hard
**Q:** How do you validate that required API keys are available using a conftest.py fixture for integration tests?
_notes: testing specifics_
- **langchain/test/integration-testing.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Integration testing
  > > Test agents with real LLM APIs by organizing tests, managing keys, handling flakiness, and controlling costs.
  > Integration tests verify that your agent works correctly with model APIs and external services. Unlike [unit tests](/oss/python/langchain/test/unit-testing) that use fakes and mocks, integration tests make actual network calls to confirm that components work together, credentials are valid, and latency is acceptable.
  > Because LLM responses are nondeterministic, integration tests require different strategies than traditional software tests. This guide covers how to organize, write, and run integration tests for your agents. For general test infrastructure when contributing to La
**A[h015]:** 

## h016 · hard
**Q:** What is the difference between unit testing and integration testing for LangChain agents?
_notes: contrast_
- **langchain/test/unit-testing.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Unit testing
  > > Test agent logic without API calls using fake chat models and in-memory persistence.
  > Unit tests exercise small, deterministic pieces of your agent in isolation. By replacing the real LLM with an in-memory fake (AKA fixture), you can script exact responses (text, tool calls, and errors) so tests are fast, free, and repeatable without API keys.
  > ## Mock chat model
  > LangChain provides [`GenericFakeChatModel`](https://reference.langchain.com/python/langchain-core/language_models/fake_chat_models/GenericFakeChatModel) for mocking text responses. It accepts an iterator of responses ([`AIMessage`](https://reference.langchain.com/python/langchain-core/messages/ai/AIMessage) objects or strings) and ret
- **langchain/test/integration-testing.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Integration testing
  > > Test agents with real LLM APIs by organizing tests, managing keys, handling flakiness, and controlling costs.
  > Integration tests verify that your agent works correctly with model APIs and external services. Unlike [unit tests](/oss/python/langchain/test/unit-testing) that use fakes and mocks, integration tests make actual network calls to confirm that components work together, credentials are valid, and latency is acceptable.
  > Because LLM responses are nondeterministic, integration tests require different strategies than traditional software tests. This guide covers how to organize, write, and run integration tests for your agents. For general test infrastructure when contributing to La
**A[h016]:** 

## h017 · hard
**Q:** How are agent evals set up according to the Agent Evals page?
_notes: evals meta_
- **langchain/test/evals.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Agent Evals
  > > Evaluate agent trajectories using deterministic matching or LLM-as-judge evaluators with AgentEvals and LangSmith.
  > Evaluations ("evals") measure how well your agent performs by assessing its execution trajectory, the sequence of messages and tool calls it produces. Unlike [integration tests](/oss/python/langchain/test/integration-testing) that verify basic correctness, evals score agent behavior against a reference or rubric, making them useful for catching regressions when you change prompts, tools, or models.
  > An evaluator is a function that takes agent outputs (and optionally reference outputs) and returns a score:
  > ```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-moc
**A[h017]:** 

## h018 · hard
**Q:** What is the difference between deep agent skills and subagents?
_notes: contrast_
- **deepagents/skills.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Skills
  > > Learn how to extend your deep agent's capabilities with skills
  > Skills package domain expertise, such as workflows, best practices, scripts, reference docs, and templates, into reusable directories. The agent gets a summary of the contents on startup and discovers and reads the contained files only when relevant.
  > Skills help you avoid context bloat by loading only summaries at startup and reading full instructions when a task requires them. You can share skills across agents and projects, and compose multiple skills in a single agent so each one covers a distinct capability.
  > <Tip>
  >   For ready-to-use skills that improve your agent's performance on LangChain ecosystem tasks, see the [LangChain Skill
- **deepagents/subagents.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Subagents
  > > Learn how to use subagents to delegate work and keep context clean
  > A deep agent can create subagents to delegate work. You can specify custom subagents in the `subagents` parameter. Subagents are useful for [context quarantine](https://www.dbreunig.com/2025/06/26/how-to-fix-your-context.html#context-quarantine) (keeping the main agent's context clean) and for providing specialized instructions.
  > This page covers **synchronous** subagents, where the supervisor blocks until the subagent finishes. For long-running tasks, parallel workstreams, or cases where you need mid-flight steering and cancellation, see [Async subagents](/oss/python/deepagents/async-subagents).
  > ```mermaid theme={"theme":{"ligh
**A[h018]:** 

## h019 · hard
**Q:** How does context engineering differ between LangChain agents and Deep Agents?
_notes: cross-product contrast_
- **langchain/context-engineering.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Context engineering in agents
  > ## Overview
  > The hard part of building agents (or any LLM application) is making them reliable enough. While they may work for a prototype, they often fail in real-world use cases.
  > ### Why do agents fail?
  > When agents fail, it's usually because the LLM call inside the agent took the wrong action / didn't do what we expected. LLMs fail for one of two reasons:
  > 1. The underlying LLM is not capable enough
  > 2. The "right" context was not passed to the LLM
  > More often than not - it's actually the second reason that causes agents to not be reliable.
  > **Context engineering** is providing the right information and tools in the right format so the LLM can accomplish a task. This is the num
- **deepagents/context-engineering.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Context engineering in Deep Agents
  > > Control what context your deep agent has access to and how it is managed across long-running tasks
  > Context engineering is providing the right information and tools in the right format so your deep agent can accomplish tasks reliably.
  > Deep agents have access to several kinds of context.
  > Some sources are provided to the agent at startup; others become available during runtime, such as user input.
  > Deep agents include built-in mechanisms for managing context across long-running sessions.
  > This page provides an overview of the different kinds of context your deep agent has access to and manages.
  > <Tip>
  >   New to context engineering? See the [conceptual overview](/oss/python/c
**A[h019]:** 

## h020 · hard
**Q:** What fault-tolerance guarantees does LangGraph provide and how are they configured?
_notes: reliability specifics_
- **langgraph/fault-tolerance.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Fault tolerance
  > > Configure per-node timeouts, retries, and error handlers in LangGraph.
  > When a node fails—from a slow external API, a transient network error, or an unhandled exception—LangGraph gives you three composable mechanisms to respond:
  > * [**Retries**](#retries) — automatically re-run failed attempts based on exception type and backoff settings
  > * [**Timeouts**](#timeouts) — cap how long a single attempt may run
  > * [**Error handling**](#error-handling) — run a recovery function after all retries are exhausted
  > Use [**`set_node_defaults`**](#graph-defaults) to configure these mechanisms once for all nodes instead of repeating them on every `add_node` call.
  > These compose in a fixed order: when a node
**A[h020]:** 

## h021 · hard
**Q:** How do async subagents differ from synchronous subagents in Deep Agents?
_notes: async nuance_
- **deepagents/async-subagents.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Async subagents
  > > Launch background subagents that run concurrently while the supervisor continues interacting with the user
  > Async subagents let a supervisor agent launch background tasks that return immediately, so the supervisor can continue interacting with the user while subagents work concurrently. The supervisor can check progress, send follow-up instructions, or cancel tasks at any point.
  > This builds on [subagents](/oss/python/deepagents/subagents), which run synchronously and block the supervisor until completion. Use async subagents when tasks are long-running, parallelizable, or need mid-flight steering.
  > <Note>
  >   Async subagents are a preview feature available in `deepagents` 0.5.0. Preview feat
- **deepagents/subagents.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Subagents
  > > Learn how to use subagents to delegate work and keep context clean
  > A deep agent can create subagents to delegate work. You can specify custom subagents in the `subagents` parameter. Subagents are useful for [context quarantine](https://www.dbreunig.com/2025/06/26/how-to-fix-your-context.html#context-quarantine) (keeping the main agent's context clean) and for providing specialized instructions.
  > This page covers **synchronous** subagents, where the supervisor blocks until the subagent finishes. For long-running tasks, parallel workstreams, or cases where you need mid-flight steering and cancellation, see [Async subagents](/oss/python/deepagents/async-subagents).
  > ```mermaid theme={"theme":{"ligh
**A[h021]:** 

## h022 · hard
**Q:** What permission controls does Deep Agents expose for tool execution?
_notes: permissions specifics_
- **deepagents/permissions.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Permissions
  > > Control filesystem access with declarative permission rules for Deep Agents
  > Control which files and directories an agent can read or write to using declarative permission rules. Pass a list of rules to `permissions=` and the agent's built-in filesystem tools respect them.
  > <Note>
  >   Permissions require `deepagents>=0.5.2`.
  > </Note>
  > Permissions only apply to the built-in filesystem tools (`ls`, `read_file`, `glob`, `grep`, `write_file`, `edit_file`). Custom tools and MCP tools that access the filesystem are not covered. Permissions also do not apply to [sandbox backends](/oss/python/deepagents/sandboxes), which support arbitrary command execution via the `execute` tool.
  > <Tip>
  >   Use `permissions
**A[h022]:** 

## h023 · hard
**Q:** How do you migrate from langgraph-supervisor to the current multi-agent approach?
_notes: migration_
- **migrate/langgraph-supervisor.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Migrate from langgraph-supervisor
  > > Migrate from the langgraph-supervisor package to the subagents pattern with create_agent and tool-wrapped subagents.
  > The [`langgraph-supervisor`](https://github.com/langchain-ai/langgraph-supervisor-py) package is no longer actively maintained. Instead use the [subagents](/oss/python/langchain/multi-agent/subagents) pattern: a main agent coordinates specialized workers by calling them as [tools](/oss/python/langchain/tools).
  > This guide covers how to migrate from `create_supervisor` to [`create_agent`](https://reference.langchain.com/python/langchain/agents/factory/create_agent), including setups that use [`interrupt`](https://reference.langchain.com/python/langgraph/type
**A[h023]:** 

## h024 · hard
**Q:** What is the recommended way to define dynamic subagents at runtime?
_notes: dynamic subagents_
- **deepagents/dynamic-subagents.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Dynamic subagents
  > > Use interpreters to dispatch and orchestrate Deep Agents subagents from code
  > Dynamic subagents let an agent dispatch [subagents](/oss/python/deepagents/subagents) from interpreter code. Instead of asking the model to choose one subagent call at a time, the agent can use JavaScript loops, branches, and parallel batches to route work across configured subagents and synthesize the results.
  > Use this pattern when work spans many independent units, needs multiple perspectives, or benefits from recursive analysis. For general interpreter setup, see [Interpreters](/oss/python/deepagents/interpreters).
  > <Warning>
  >   Dynamic subagents use the interpreter runtime, which is in [**beta**](/oss/python
**A[h024]:** 

## h025 · hard
**Q:** What does event streaming (stream_mode events) expose that message streaming does not?
_notes: streaming modes contrast_
- **langchain/event-streaming.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Event streaming
  > > Stream real-time updates from LangChain agent runs
  > LangChain agents are built on LangGraph, so they support the same streaming stack with agent-focused projections for messages, tool calls, state, and custom updates.
  > For most application and frontend use cases, use **Event Streaming** through `stream_events(..., version="v3")`. Event Streaming returns a run object with typed projections, so each projection can be consumed independently instead of parsing stream-mode tuples.
  > ```py theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
  > from langchain.agents import create_agent
  > 
  > def get_weather(city: str) -> str:
  >     """Get weather for a city."""
  >     return f"It's always su
- **langchain/streaming.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Streaming
  > > Stream real-time updates from agent runs
  > <Tip>
  >   For new applications, we recommend [event streaming](/oss/python/langchain/event-streaming)—the typed-projection API introduced in LangChain v1.3. Event streaming gives you separate iterators per projection (messages, values, tool calls, subgraphs) so you can consume them independently instead of branching on `stream_mode` chunks.
  > </Tip>
  > LangChain implements a streaming system to surface real-time updates.
  > Streaming is crucial for enhancing the responsiveness of applications built on LLMs. By displaying output progressively, even before a complete response is ready, streaming significantly improves user experience (UX), particularly when dealing
**A[h025]:** 

## h026 · hard
**Q:** How do you persist deep-agent memory across sessions using the code memory-and-skills backend?
_notes: deep agents code_
- **deepagents/code/memory-and-skills.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Memory and Skills
  > > Persistent memory, AGENTS.md files, and reusable skills for Deep Agents Code, including creation, discovery, and invocation.
  > There are two primary ways to customize an agent in Deep Agents Code:
  > * **[Memory](#memory)**: `AGENTS.md` files and auto-saved memories that persist across sessions. Use memory for general coding style, preferences, and learned conventions.
  > * **[Skills](#skills)**: Reusable, on-demand capabilities that the agent discovers and reads only when relevant. Use skills for task-specific context such as workflows, best practices, and reference docs.
  > In practice, skills and memory sit on a spectrum. For more on when to use each, see [Skills, memory, and tools](/oss/pyth
**A[h026]:** 

## h027 · hard
**Q:** What are the components of a grading rubric for a deep agent, per the rubric docs?
_notes: rubric structure_
- **deepagents/rubric.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Grading rubrics
  > > LLM-as-a-judge grading for agents that iterate against a rubric until done
  > <Note>
  >   `RubricMiddleware` requires `deepagents>=0.6.5`. It is in [**beta**](/oss/python/versioning); the API may change in the future.
  > </Note>
  > Some agent tasks have a clear definition of "done" that the working model alone cannot reliably hit on the first try: a haiku in the right syllable pattern, a refactor with all tests passing, a report that hits every required section. `RubricMiddleware` lets you declare *what done looks like* as a rubric and have the agent **self-evaluate and iterate**  until the rubric is satisfied (or a configured maximum iteration cap is hit).
  > **LLM-as-a-judge** is a pattern where one
**A[h027]:** 

## h028 · hard
**Q:** How does the guardrails middleware interact with tool calls to block disallowed actions?
_notes: cross-page mechanism_
- **langchain/guardrails.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Guardrails
  > > Implement safety checks and content filtering for your agents
  > Guardrails help you build safe, compliant AI applications by validating and filtering content at key points in your agent's execution. They can detect sensitive information, enforce content policies, validate outputs, and prevent unsafe behaviors before they cause problems.
  > Common use cases include:
  > * Preventing PII leakage
  > * Detecting and blocking prompt injection attacks
  > * Blocking inappropriate or harmful content
  > * Enforcing business rules and compliance requirements
  > * Validating output quality and accuracy
  > You can implement guardrails using [middleware](/oss/python/langchain/middleware) to intercept execution at strategic poin
- **langchain/middleware/custom.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Custom middleware
  > Build custom middleware by implementing hooks that run at specific points in the agent execution flow.
  > ## Hooks
  > Middleware provides two styles of hooks to intercept agent execution:
  > <CardGroup cols={2}>
  >   <Card title="Node-style hooks" icon="share" href="#node-style-hooks">
  >     Run sequentially at specific execution points.
  >   </Card>
  >   <Card title="Wrap-style hooks" icon="container" href="#wrap-style-hooks">
  >     Run around each model or tool call.
  >   </Card>
  > </CardGroup>
  > ### Node-style hooks
  > Run sequentially at specific execution points. Use for logging, validation, and state updates.
  > Choose the hooks your middleware needs. You can choose between node-style hooks and wrap-style hooks.
**A[h028]:** 

## m001 · multi-hop
**Q:** To build an agent that remembers user preferences across conversations and can look them up inside a tool, which memory mechanism do you use and how does a tool access it?
_notes: store + tool runtime, 3 pages_
- **langchain/long-term-memory.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Long-term memory
  > > Add long-term memory to LangChain agents to store and recall data across conversations and sessions
  > Long-term memory lets your agent store and recall information across different conversations and sessions.
  > Unlike [short-term memory](/oss/python/langchain/short-term-memory), which is scoped to a single thread, long-term memory persists across threads and can be recalled at any time.
  > Long-term memory is built on [LangGraph stores](/oss/python/langgraph/stores), which save data as JSON documents organized by namespace and key.
  > ## Usage
  > To add long-term memory to an agent, create a store and pass it to [`create_agent`](https://reference.langchain.com/python/langchain/agents/factory/create_
- **langgraph/stores.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Stores
  > > LangGraph stores provide cross-thread long-term memory, complementing per-thread checkpointer persistence.
  > Stores let agents persist information across threads, including user preferences, accumulated knowledge, and facts that should survive beyond a single conversation. Unlike [checkpointers](/oss/python/langgraph/checkpointers), which save the full graph state scoped to one thread, stores hold arbitrary key-value data accessible from any thread.
  > <img src="https://mintcdn.com/langchain-5e9cc07a/dL5Sn6Cmy9pwtY0V/oss/images/shared_state.png?fit=max&auto=format&n=dL5Sn6Cmy9pwtY0V&q=85&s=354526fb48c5eb11b4b2684a2df40d6c" alt="Model of shared state" width="1482" height="777" data-path="oss/images/shar
- **langchain/tools.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Tools
  > Tools extend what [agents](/oss/python/langchain/agents) can do—letting them fetch real-time data, execute code, query external databases, and take actions in the world.
  > Under the hood, tools are callable functions with well-defined inputs and outputs that get passed to a [chat model](/oss/python/langchain/models). The model decides when to invoke a tool based on the conversation context, and what input arguments to provide.
  > <Tip>
  >   For details on how models handle tool calls, see [Tool calling](/oss/python/langchain/models#tool-calling). Trace tool calls and debug errors with [LangSmith](https://smith.langchain.com?utm_source=docs\&utm_medium=cta\&utm_campaign=langsmith-signup\&utm_content=oss-langc
**A[m001]:** 

## m002 · multi-hop
**Q:** How do you build a customer-support system where one agent hands off to a specialist and the conversation state is preserved across the handoff?
_notes: handoffs + persistence_
- **langchain/multi-agent/handoffs-customer-support.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Build customer support with handoffs
  > The [state machine pattern](/oss/python/langchain/multi-agent/handoffs) describes workflows where an agent's behavior changes as it moves through different states of a task. This tutorial shows how to implement a state machine by using tool calls to dynamically change a single agent's configuration—updating its available tools and instructions based on the current state. The state can be determined from multiple sources: the agent's past actions (tool calls), external state (such as API call results), or even initial user input (for example, by running a classifier to determine user intent).
  > In this tutorial, you'll build a customer support agent that does the following:
- **langchain/multi-agent/handoffs.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Handoffs
  > In the **handoffs** architecture, behavior changes dynamically based on state. The core mechanism: [tools](/oss/python/langchain/tools) update a state variable (e.g., `current_step` or `active_agent`) that persists across turns, and the system reads this variable to adjust behavior—either applying different configuration (system prompt, tools) or routing to a different [agent](/oss/python/langchain/agents). This pattern supports both handoffs between distinct agents and dynamic configuration changes within a single agent.
  > <Tip>
  >   The term **handoffs** was coined by [OpenAI](https://openai.github.io/openai-agents-python/handoffs/) for using tool calls (e.g., `transfer_to_sales_agent`) to transfer co
- **langgraph/persistence.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Persistence
  > > LangGraph's persistence layer gives agents short-term memory through checkpointers and long-term memory through stores.
  > <a id="checkpoints" />
  > <a id="threads" />
  > <a id="memory-store" />
  > <a id="checkpointer-libraries" />
  > <a id="pending-writes" />
  > <a id="durability-modes" />
  > Persistence lets LangGraph applications keep useful information beyond a single graph run. It matters when an agent needs to continue a conversation, resume after an interruption, recover from a failure, or remember information across interactions.
  > LangGraph provides two complementary persistence systems:
  > * **[Checkpointers](/oss/python/langgraph/checkpointers)** persist a thread's graph state as checkpoints. Use the
**A[m002]:** 

## m003 · multi-hop
**Q:** How do you stream an agent's LLM tokens to a frontend while also allowing human-in-the-loop approval of tool calls?
_notes: streaming + HITL_
- **langchain/streaming.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Streaming
  > > Stream real-time updates from agent runs
  > <Tip>
  >   For new applications, we recommend [event streaming](/oss/python/langchain/event-streaming)—the typed-projection API introduced in LangChain v1.3. Event streaming gives you separate iterators per projection (messages, values, tool calls, subgraphs) so you can consume them independently instead of branching on `stream_mode` chunks.
  > </Tip>
  > LangChain implements a streaming system to surface real-time updates.
  > Streaming is crucial for enhancing the responsiveness of applications built on LLMs. By displaying output progressively, even before a complete response is ready, streaming significantly improves user experience (UX), particularly when dealing
- **langchain/human-in-the-loop.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Human-in-the-loop
  > The Human-in-the-Loop (HITL) [middleware](/oss/python/langchain/middleware/built-in#human-in-the-loop) lets you add human oversight to agent tool calls.
  > When a model proposes an action that might require review—for example, writing to a file or executing SQL—the middleware can pause execution and wait for a decision.
  > It does this by checking each tool call against a configurable policy. If intervention is needed, the middleware issues an [interrupt](https://reference.langchain.com/python/langgraph/types/interrupt) that halts execution. The graph state is saved using LangGraph's [persistence layer](/oss/python/langgraph/persistence), so execution can pause safely and resume later.
  > A human
- **langchain/frontend/human-in-the-loop.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Human-in-the-Loop
  > > Add approval workflows with interrupt-based human review
  > export const PatternEmbed = ({pattern, id, theme, height, minHeight = 400, maxHeight = 700, className, defaultView = "preview", defaultSdk = "react", defaultLanguage = "js", showCodeTab = true, agentServer = "prod", onError, onReady}) => {
  >   var VALID_GUEST_TYPES = new Set(["READY", "RESIZE", "ERROR", "RUN_STARTED", "TRACE_URL", "THREAD_CLEARED"]);
  >   function stub() {
  >     return {
  >       safeParse: data => ({
  >         success: true,
  >         data
  >       }),
  >       optional: () => stub(),
  >       min: () => stub(),
  >       url: () => stub()
  >     };
  >   }
  >   var z = {
  >     object: _shape => stub(),
  >     literal: _value => stub(),
  >     string: () => s
**A[m003]:** 

## m004 · multi-hop
**Q:** How would you build a RAG agent and add persistent conversational memory to it?
_notes: rag + memory_
- **langchain/rag.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Build a RAG agent with LangChain
  > One of the most powerful LLM-based applications are sophisticated question-answering (Q\&A) chatbots which augment LLMs by providing it with structured access to a set of data.
  > This might be private data, recent data, or data that is not part of the training data the LLM is trained on.
  > These applications use a technique known as Retrieval Augmented Generation, or [RAG](/oss/python/langchain/retrieval/).
  > This tutorial will guide you through building an app that answers questions about a long unstructured text:
  > 1. **[Indexing content](#index-your-content)**: Creating a pipeline for ingesting data from a source and indexing it.
  > 2. **[RAG agent](#rag-agent)**: A general-purpose
- **langgraph/add-memory.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Memory
  > AI applications need [memory](/oss/python/concepts/memory) to share context across multiple interactions. In LangGraph, you can add two types of memory:
  > * [Add short-term memory](#add-short-term-memory) as a part of your agent's [state](/oss/python/langgraph/graph-api#state) to enable multi-turn conversations.
  > * [Add long-term memory](#add-long-term-memory) to store user-specific or application-level data across sessions.
  > ## Add short-term memory
  > **Short-term** memory (thread-level [persistence](/oss/python/langgraph/persistence)) enables agents to track multi-turn conversations. To add short-term memory:
  > ```python theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
  > from langgrap
**A[m004]:** 

## m005 · multi-hop
**Q:** How do you build a SQL agent and add guardrails so it cannot run destructive statements?
_notes: sql-agent + guardrails_
- **langchain/sql-agent.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Build a SQL agent
  > ## Overview
  > In this tutorial, you will learn how to build an agent that can answer questions about a SQL database using LangChain [agents](/oss/python/langchain/agents).
  > At a high level, the agent will:
  > 1. Fetch the available tables and schemas from the database
  > 2. Decide which tables are relevant to the question
  > 3. Fetch the schemas for the relevant tables
  > 4. Generate a query based on the question and information from the schemas
  > 5. Double-check the query for common mistakes using an LLM
  > 6. Execute the query and return the results
  > 7. Correct mistakes surfaced by the database engine until the query is successful
  > 8. Formulate a response based on the results
  > <Warning>
  >   Building Q\&A syste
- **langchain/guardrails.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Guardrails
  > > Implement safety checks and content filtering for your agents
  > Guardrails help you build safe, compliant AI applications by validating and filtering content at key points in your agent's execution. They can detect sensitive information, enforce content policies, validate outputs, and prevent unsafe behaviors before they cause problems.
  > Common use cases include:
  > * Preventing PII leakage
  > * Detecting and blocking prompt injection attacks
  > * Blocking inappropriate or harmful content
  > * Enforcing business rules and compliance requirements
  > * Validating output quality and accuracy
  > You can implement guardrails using [middleware](/oss/python/langchain/middleware) to intercept execution at strategic poin
**A[m005]:** 

## m006 · multi-hop
**Q:** How do you resume a paused (interrupted) graph after a human approves, and where is the paused state stored?
_notes: interrupts + persistence + checkpointers_
- **langgraph/interrupts.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Interrupts
  > Interrupts allow you to pause graph execution at specific points and wait for external input before continuing. This enables human-in-the-loop patterns where you need external input to proceed. When an interrupt is triggered, LangGraph saves the graph state using its [persistence](/oss/python/langgraph/persistence) layer and waits indefinitely until you resume execution.
  > Interrupts work by calling the `interrupt()` function at any point in your graph nodes. The function accepts any JSON-serializable value which is surfaced to the caller. When you're ready to continue, you resume execution by re-invoking the graph using `Command`, which then becomes the return value of the `interrupt()` call from
- **langgraph/persistence.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Persistence
  > > LangGraph's persistence layer gives agents short-term memory through checkpointers and long-term memory through stores.
  > <a id="checkpoints" />
  > <a id="threads" />
  > <a id="memory-store" />
  > <a id="checkpointer-libraries" />
  > <a id="pending-writes" />
  > <a id="durability-modes" />
  > Persistence lets LangGraph applications keep useful information beyond a single graph run. It matters when an agent needs to continue a conversation, resume after an interruption, recover from a failure, or remember information across interactions.
  > LangGraph provides two complementary persistence systems:
  > * **[Checkpointers](/oss/python/langgraph/checkpointers)** persist a thread's graph state as checkpoints. Use the
- **langgraph/checkpointers.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Checkpointers
  > > LangGraph checkpointers save graph state as checkpoints at each step, enabling persistence, human-in-the-loop, and fault-tolerant execution.
  > A checkpointer saves a snapshot of graph state at each super-step, organized into **threads**. Compile a graph with a checkpointer to enable human-in-the-loop workflows, time travel debugging, fault-tolerant execution, and conversational memory.
  > <img src="https://mintcdn.com/langchain-5e9cc07a/-_xGPoyjhyiDWTPJ/oss/images/checkpoints.jpg?fit=max&auto=format&n=-_xGPoyjhyiDWTPJ&q=85&s=966566aaae853ed4d240c2d0d067467c" alt="Checkpoints" width="2316" height="748" data-path="oss/images/checkpoints.jpg" />
  > <Info>
  >   **Agent Server handles checkpointing automa
**A[m006]:** To resume a graph paused with `interrupt()`, you send `Command(resume=...)` back into the graph using the same config (matching `thread_id`), and the value passed becomes the return value of the `interrupt()` call; the paused state is not ephemeral but persisted by the checkpointer (e.g. `InMemorySaver`, or a durable checkpointer in production) keyed on that `thread_id`, saved at the moment `interrupt()` is hit so it can later be retrieved and resumed from where it left off.

## m007 · multi-hop
**Q:** How do you create a deep agent that uses subagents and persists their memory across runs?
_notes: deep agent + subagents + memory_
- **deepagents/quickstart.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Quickstart
  > > Build your first deep agent in minutes
  > This guide walks you through creating your first deep agent with planning, file system tools, and subagent capabilities. You'll build a research agent that can conduct research and write reports.
  > <Tip>
  >   **Using an AI coding assistant?**
  >   * Install the [LangChain Docs MCP server](/use-these-docs) to give your agent access to up-to-date LangChain documentation and examples.
  >   * Install [LangChain Skills](https://github.com/langchain-ai/langchain-skills) to improve your agent's performance on LangChain ecosystem tasks.
  > </Tip>
  > ## Prerequisites
  > Before you begin, make sure you have an API key from a model provider (e.g., Gemini, Anthropic, OpenAI).
  > <Note>
- **deepagents/subagents.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Subagents
  > > Learn how to use subagents to delegate work and keep context clean
  > A deep agent can create subagents to delegate work. You can specify custom subagents in the `subagents` parameter. Subagents are useful for [context quarantine](https://www.dbreunig.com/2025/06/26/how-to-fix-your-context.html#context-quarantine) (keeping the main agent's context clean) and for providing specialized instructions.
  > This page covers **synchronous** subagents, where the supervisor blocks until the subagent finishes. For long-running tasks, parallel workstreams, or cases where you need mid-flight steering and cancellation, see [Async subagents](/oss/python/deepagents/async-subagents).
  > ```mermaid theme={"theme":{"ligh
- **deepagents/memory.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Memory
  > > Add persistent memory to agents built with Deep Agents so they learn and improve across conversations
  > Memory lets your agent learn and improve across conversations. Deep Agents makes memory first class with filesystem-backed memory: the agent reads and writes memory as files, and you control where those files are stored using [backends](/oss/python/deepagents/backends).
  > <Note>
  >   This page covers **long-term memory**: memory that persists across conversations. For short-term memory (conversation history and scratch files within a single session), see the [context engineering](/oss/python/deepagents/context-engineering) guide. Short-term memory is managed automatically as part of the agent's [state]
**A[m007]:** 

## m008 · multi-hop
**Q:** How do you route a query to the right knowledge source and then generate a grounded answer with citations?
_notes: router + rag_
- **langchain/multi-agent/router-knowledge-base.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Build a multi-source knowledge base with routing
  > ## Overview
  > The **router pattern** is a [multi-agent](/oss/python/langchain/multi-agent) architecture where a routing step classifies input and directs it to specialized agents, with results synthesized into a combined response. This pattern excels when your organization's knowledge lives across distinct **verticals** (separate knowledge domains that each require their own agent with specialized tools and prompts).
  > In this tutorial, you'll build a multi-source knowledge base router that demonstrates these benefits through a realistic enterprise scenario. The system will coordinate three specialists:
  > * A **GitHub agent** that searches code, issues, and pull r
- **langchain/rag.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Build a RAG agent with LangChain
  > One of the most powerful LLM-based applications are sophisticated question-answering (Q\&A) chatbots which augment LLMs by providing it with structured access to a set of data.
  > This might be private data, recent data, or data that is not part of the training data the LLM is trained on.
  > These applications use a technique known as Retrieval Augmented Generation, or [RAG](/oss/python/langchain/retrieval/).
  > This tutorial will guide you through building an app that answers questions about a long unstructured text:
  > 1. **[Indexing content](#index-your-content)**: Creating a pipeline for ingesting data from a source and indexing it.
  > 2. **[RAG agent](#rag-agent)**: A general-purpose
**A[m008]:** 

## m009 · multi-hop
**Q:** How do you add custom middleware that logs every tool call and also enforces a timeout, using both hooks?
_notes: middleware multi-hook_
- **langchain/middleware/custom.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Custom middleware
  > Build custom middleware by implementing hooks that run at specific points in the agent execution flow.
  > ## Hooks
  > Middleware provides two styles of hooks to intercept agent execution:
  > <CardGroup cols={2}>
  >   <Card title="Node-style hooks" icon="share" href="#node-style-hooks">
  >     Run sequentially at specific execution points.
  >   </Card>
  >   <Card title="Wrap-style hooks" icon="container" href="#wrap-style-hooks">
  >     Run around each model or tool call.
  >   </Card>
  > </CardGroup>
  > ### Node-style hooks
  > Run sequentially at specific execution points. Use for logging, validation, and state updates.
  > Choose the hooks your middleware needs. You can choose between node-style hooks and wrap-style hooks.
- **langchain/middleware/overview.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Overview
  > > Control and customize agent execution at every step
  > Middleware provides a way to more tightly control what happens inside the agent. Middleware is useful for the following:
  > * Tracking agent behavior with logging, analytics, and debugging.
  > * Transforming prompts, [tool selection](/oss/python/langchain/middleware/built-in#llm-tool-selector), and output formatting.
  > * Adding [retries](/oss/python/langchain/middleware/built-in#tool-retry), [fallbacks](/oss/python/langchain/middleware/built-in#model-fallback), and early termination logic.
  > * Applying [rate limits](/oss/python/langchain/middleware/built-in#model-call-limit), guardrails, and [PII detection](/oss/python/langchain/middleware/built-in#pii-d
**A[m009]:** 

## m010 · multi-hop
**Q:** How do you migrate an existing LangChain v0 agent to v1 and update the way middleware replaces the old model/state configuration?
_notes: migration + middleware_
- **migrate/langchain-v1.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # LangChain v1 migration guide
  > This guide outlines the major changes between [LangChain v1](/oss/python/releases/langchain-v1) and previous versions.
  > ### `langchain-classic`
  > If you were using any of the following from the `langchain` package, you'll need to install [`langchain-classic`](https://pypi.org/project/langchain-classic/) and update your imports:
  > * Legacy chains (`LLMChain`, `ConversationChain`, etc.)
  > * Retrievers (e.g. `MultiQueryRetriever` or anything from the previous `langchain.retrievers` module)
  > * The indexing API
  > * The hub module (for managing prompts programmatically)
  > * Embeddings modules (e.g. `CacheBackedEmbeddings` and community embeddings)
  > * [`langchain-community`](https://pypi.org/proje
- **langchain/middleware/overview.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Overview
  > > Control and customize agent execution at every step
  > Middleware provides a way to more tightly control what happens inside the agent. Middleware is useful for the following:
  > * Tracking agent behavior with logging, analytics, and debugging.
  > * Transforming prompts, [tool selection](/oss/python/langchain/middleware/built-in#llm-tool-selector), and output formatting.
  > * Adding [retries](/oss/python/langchain/middleware/built-in#tool-retry), [fallbacks](/oss/python/langchain/middleware/built-in#model-fallback), and early termination logic.
  > * Applying [rate limits](/oss/python/langchain/middleware/built-in#model-call-limit), guardrails, and [PII detection](/oss/python/langchain/middleware/built-in#pii-d
**A[m010]:** 

## m011 · multi-hop
**Q:** How do you test an agent's tool-calling behavior with unit tests and then validate it end-to-end with integration tests requiring real keys?
_notes: testing pipeline_
- **langchain/test/unit-testing.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Unit testing
  > > Test agent logic without API calls using fake chat models and in-memory persistence.
  > Unit tests exercise small, deterministic pieces of your agent in isolation. By replacing the real LLM with an in-memory fake (AKA fixture), you can script exact responses (text, tool calls, and errors) so tests are fast, free, and repeatable without API keys.
  > ## Mock chat model
  > LangChain provides [`GenericFakeChatModel`](https://reference.langchain.com/python/langchain-core/language_models/fake_chat_models/GenericFakeChatModel) for mocking text responses. It accepts an iterator of responses ([`AIMessage`](https://reference.langchain.com/python/langchain-core/messages/ai/AIMessage) objects or strings) and ret
- **langchain/test/integration-testing.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Integration testing
  > > Test agents with real LLM APIs by organizing tests, managing keys, handling flakiness, and controlling costs.
  > Integration tests verify that your agent works correctly with model APIs and external services. Unlike [unit tests](/oss/python/langchain/test/unit-testing) that use fakes and mocks, integration tests make actual network calls to confirm that components work together, credentials are valid, and latency is acceptable.
  > Because LLM responses are nondeterministic, integration tests require different strategies than traditional software tests. This guide covers how to organize, write, and run integration tests for your agents. For general test infrastructure when contributing to La
**A[m011]:** 

## m012 · multi-hop
**Q:** How do you build a voice agent that streams responses and maintains short-term memory of the conversation?
_notes: voice + streaming + memory_
- **langchain/voice-agent.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Build a voice agent with LangChain
  > ## Overview
  > Chat interfaces have dominated how we interact with AI, but recent breakthroughs in multimodal AI are opening up exciting new possibilities. High-quality generative models and expressive text-to-speech (TTS) systems now make it possible to build agents that feel less like tools and more like conversational partners.
  > Voice agents are one example of this. Instead of relying on a keyboard and mouse to type inputs into an agent, you can use spoken words to interact with it. This can be a more natural and engaging way to interact with AI, and can be especially useful for certain contexts.
  > ### What are voice agents?
  > Voice agents are [agents](/oss/python/langchain/ag
- **langchain/streaming.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Streaming
  > > Stream real-time updates from agent runs
  > <Tip>
  >   For new applications, we recommend [event streaming](/oss/python/langchain/event-streaming)—the typed-projection API introduced in LangChain v1.3. Event streaming gives you separate iterators per projection (messages, values, tool calls, subgraphs) so you can consume them independently instead of branching on `stream_mode` chunks.
  > </Tip>
  > LangChain implements a streaming system to surface real-time updates.
  > Streaming is crucial for enhancing the responsiveness of applications built on LLMs. By displaying output progressively, even before a complete response is ready, streaming significantly improves user experience (UX), particularly when dealing
- **langchain/short-term-memory.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Short-term memory
  > ## Overview
  > Memory is a system that remembers information about previous interactions. For AI agents, memory is crucial because it lets them remember previous interactions, learn from feedback, and adapt to user preferences. As agents tackle more complex tasks with numerous user interactions, this capability becomes essential for both efficiency and user satisfaction.
  > Short term memory lets your application remember previous interactions within a single thread or conversation.
  > <Note>
  >   A thread organizes multiple interactions in a session, similar to the way email groups messages in a single conversation.
  > </Note>
  > Conversation history is the most common form of short-term memory. Long con
**A[m012]:** 

## m013 · multi-hop
**Q:** How do you deploy a LangGraph app locally for development and then to production?
_notes: local + deploy_
- **langgraph/local-server.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Run a local server
  > This guide shows you how to run a LangGraph application locally.
  > ## Prerequisites
  > Before you begin, ensure you have the following:
  > * An API key for [LangSmith](https://smith.langchain.com/settings) - free to sign up
  > ## 1. Install the LangGraph CLI
  > <CodeGroup>
  >   ```bash pip theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
  >   # Python >= 3.11 is required.
  >   pip install -U "langgraph-cli[inmem]"
  >   ```
  >   ```bash uv theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
  >   # Python >= 3.11 is required.
  >   uv add "langgraph-cli[inmem]"
  >   ```
  > </CodeGroup>
  > ## 2. Create a LangGraph app
  > Create a new app from the [`new-langgraph-project-python` template](https:
- **langgraph/deploy.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Deployment
  > > Deploy LangGraph agents to production with LangSmith Cloud or JavaScript frameworks and hosting platforms.
  > When you are ready to deploy your LangGraph agent to production, choose a hosting model that fits your stack. **[LangSmith Cloud](/langsmith/deploy-to-cloud)** provides fully managed infrastructure for stateful, long-running agents with persistent state and background execution.
  > <Tip>
  >   LangSmith offers multiple deployment options beyond Cloud, including [hybrid](/langsmith/hybrid), [standalone servers](/langsmith/deploy-standalone-server), and [self-hosted with control plane](/langsmith/deploy-with-control-plane). For more information, see the [LangSmith Deployment overview](/langsmith/d
**A[m013]:** 

## m014 · multi-hop
**Q:** How do you build a data-analysis deep agent that runs code in a sandbox and returns results to the user?
_notes: data analysis + sandbox_
- **deepagents/data-analysis.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Build a data analysis agent
  > > Build an agent that analyzes data files, generates visualizations, and shares results
  > ## Overview
  > This guide demonstrates how to build a data analysis agent using a [deep agent](/oss/python/deepagents). Data analysis tasks typically require planning, code execution, and working with artifacts such as scripts, reports, and plots—capabilities that deep agents are designed to handle.
  > The agent we'll build will:
  > 1. Accept a CSV file for analysis
  > 2. Perform exploratory data analysis and generate visualizations
  > 3. Share results to a Slack channel
  > <Tip>
  >   The Slack integration is optional. The agent can be modified to save artifacts locally or share results through other channels.
- **deepagents/sandboxes.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Sandboxes
  > > Execute code in isolated environments with sandbox backends
  > Agents generate code, interact with filesystems, and run shell commands. Because we can't predict what an agent might do, it's important that its environment is isolated so it can't access credentials, files, or the network. Sandboxes provide this isolation by creating a boundary between the agent's execution environment and your host system.
  > In Deep Agents, **sandboxes are [backends](/oss/python/deepagents/backends)** that define the environment where the agent operates. Unlike other backends (State, Filesystem, Store) which only expose file operations, sandbox backends also give the agent an `execute` tool for running shell commands.
**A[m014]:** 

## m015 · multi-hop
**Q:** How do you combine subgraphs with checkpointing so each subgraph keeps its own persistent state?
_notes: subgraphs + checkpointers_
- **langgraph/use-subgraphs.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Subgraphs
  > This guide explains the mechanics of using subgraphs. A subgraph is a [graph](/oss/python/langgraph/graph-api#graphs) that is used as a [node](/oss/python/langgraph/graph-api#nodes) in another graph.
  > Subgraphs are useful for:
  > * Building [multi-agent systems](/oss/python/langchain/multi-agent)
  > * Reusing a set of nodes in multiple graphs
  > * Distributing development: when you want different teams to work on different parts of the graph independently, you can define each part as a subgraph, and as long as the subgraph interface (the input and output schemas) is respected, the parent graph can be built without knowing any details of the subgraph
  > ## Setup
  > <CodeGroup>
  >   ```bash pip theme={"theme":{"ligh
- **langgraph/checkpointers.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Checkpointers
  > > LangGraph checkpointers save graph state as checkpoints at each step, enabling persistence, human-in-the-loop, and fault-tolerant execution.
  > A checkpointer saves a snapshot of graph state at each super-step, organized into **threads**. Compile a graph with a checkpointer to enable human-in-the-loop workflows, time travel debugging, fault-tolerant execution, and conversational memory.
  > <img src="https://mintcdn.com/langchain-5e9cc07a/-_xGPoyjhyiDWTPJ/oss/images/checkpoints.jpg?fit=max&auto=format&n=-_xGPoyjhyiDWTPJ&q=85&s=966566aaae853ed4d240c2d0d067467c" alt="Checkpoints" width="2316" height="748" data-path="oss/images/checkpoints.jpg" />
  > <Info>
  >   **Agent Server handles checkpointing automa
**A[m015]:** 

## m016 · multi-hop
**Q:** How do you wire an MCP tool server into an agent and expose its tools to the model?
_notes: mcp + tools_
- **langchain/mcp.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Model Context Protocol (MCP)
  > [Model Context Protocol (MCP)](https://modelcontextprotocol.io/introduction) is an open protocol that standardizes how applications provide tools and context to LLMs. LangChain agents can use tools defined on MCP servers using the [`langchain-mcp-adapters`](https://github.com/langchain-ai/langchain-mcp-adapters) library.
  > ## Quickstart
  > Install the `langchain-mcp-adapters` library:
  > <CodeGroup>
  >   ```bash pip theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
  >   pip install langchain-mcp-adapters
  >   ```
  > ```bash uv theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
  >   uv add langchain-mcp-adapters
  >   ```
  > </CodeGroup>
  > `langchain-mcp-adapters` ena
- **langchain/tools.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Tools
  > Tools extend what [agents](/oss/python/langchain/agents) can do—letting them fetch real-time data, execute code, query external databases, and take actions in the world.
  > Under the hood, tools are callable functions with well-defined inputs and outputs that get passed to a [chat model](/oss/python/langchain/models). The model decides when to invoke a tool based on the conversation context, and what input arguments to provide.
  > <Tip>
  >   For details on how models handle tool calls, see [Tool calling](/oss/python/langchain/models#tool-calling). Trace tool calls and debug errors with [LangSmith](https://smith.langchain.com?utm_source=docs\&utm_medium=cta\&utm_campaign=langsmith-signup\&utm_content=oss-langc
**A[m016]:** thorough the langchain-mcp-adapters library,, we need to create a MultiServerMCPClient, and retrieve the tools server has to offer, and than pass the resulting loo list to our agents through create_deep_agent_ or create_agent

## m017 · multi-hop
**Q:** How do you build a multi-agent supervisor workflow and stream its intermediate steps to a UI?
_notes: workflow + streaming_
- **langchain/multi-agent/custom-workflow.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Custom workflow
  > In the **custom workflow** architecture, you define your own bespoke execution flow using [LangGraph](/oss/python/langgraph/overview). You have complete control over the graph structure—including sequential steps, conditional branches, loops, and parallel execution.
  > ```mermaid theme={"theme":{"light":"catppuccin-latte","dark":"catppuccin-mocha"}}
  > graph LR
  >     A([Input]) --> B{{Conditional}}
  >     B -->|path_a| C[Deterministic step]
  >     B -->|path_b| D((Agentic step))
  >     C --> G([Output])
  >     D --> G([Output])
  >     classDef trigger fill:#F6FFDB,stroke:#6E8900,stroke-width:2px,color:#2E3900
  >     classDef process fill:#E5F4FF,stroke:#006DDD,stroke-width:2px,color:#030710
  >     classDef decision fil
- **langgraph/streaming.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Streaming
  > <Tip>
  >   For new applications, we recommend [event streaming](/oss/python/langgraph/event-streaming)—the typed-projection API introduced in LangGraph v1.2. Event streaming gives you separate iterators per projection (messages, values, subgraphs, output) so you can consume them independently instead of branching on `stream_mode` chunks.
  > </Tip>
  > This page covers LangGraph's stream-mode API. It exposes graph execution through stream modes such as `updates`, `values`, `messages`, `custom`, `checkpoints`, `tasks`, and `debug`. Use it when you need direct access to graph-runtime events or specific stream-mode output.
  > ## Get started
  > ### Basic usage
  > LangGraph graphs expose the [`stream`](https://reference.
**A[m017]:** it requires two parts: graph architecture, and event streaming api. In backend, the central supervisor which wil oing to act as a router, orchestrator must be set up. It will use handoff tools to route tasks to worker agents.

## m018 · multi-hop
**Q:** How do you produce structured output from an agent and validate it, then stream partial structured results to the frontend?
_notes: structured output + frontend_
- **langchain/structured-output.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Structured output
  > Structured output allows agents to return data in a specific, predictable format. Instead of parsing natural language responses, you get structured data in the form of JSON objects, [Pydantic models](https://docs.pydantic.dev/latest/concepts/models/#basic-model-usage), or dataclasses that your application can use directly.
  > <Tip>
  >   This page covers structured output with agents using `create_agent`. To use structured output directly on a model (outside of agents), see [Models - Structured output](/oss/python/langchain/models#structured-output).
  > </Tip>
  > LangChain's [`create_agent`](https://reference.langchain.com/python/langchain/agents/factory/create_agent) handles structured output automat
- **langchain/frontend/structured-output.md**:
  > > ## Documentation Index
  > > Fetch the complete documentation index at: https://docs.langchain.com/llms.txt
  > > Use this file to discover all available pages before exploring further.
  > # Structured output
  > > Render structured agent responses with custom UI components instead of plain text
  > export const PatternEmbed = ({pattern, id, theme, height, minHeight = 400, maxHeight = 700, className, defaultView = "preview", defaultSdk = "react", defaultLanguage = "js", showCodeTab = true, agentServer = "prod", onError, onReady}) => {
  >   var VALID_GUEST_TYPES = new Set(["READY", "RESIZE", "ERROR", "RUN_STARTED", "TRACE_URL", "THREAD_CLEARED"]);
  >   function stub() {
  >     return {
  >       safeParse: data => ({
  >         success: true,
  >         data
  >       }),
  >       optional: () => stub(),
  >       min: () => stub(),
  >       url: () => stub()
  >     };
  >   }
  >   var z = {
  >     object: _shape => stub(),
  >     literal: _value => st
**A[m018]:** To produce and validate structured output from an agent, Pydantics standard model response_format must be configured. Agent would than return the structured_response key of its state.

## u001 · unanswerable
**Q:** What is the monthly price of LangSmith's Plus plan?
_notes: pricing not in /oss/python docs — must say not in corpus_
> (unanswerable — expected behavior: decline / 'not in the corpus')
**A[u001]:** The provided documentation excerpts do not specify any information about the question asked.

## u002 · unanswerable
**Q:** How do I use create_agent in the JavaScript/TypeScript SDK?
_notes: corpus is /oss/python only; JS excluded by scope_
> (unanswerable — expected behavior: decline / 'not in the corpus')
**A[u002]:** The provided documentation excerpts do not specify any information about the question asked.

## u003 · unanswerable
**Q:** Which is better for RAG, LangChain or LlamaIndex?
_notes: comparison to external framework — corpus-gap / opinion_
> (unanswerable — expected behavior: decline / 'not in the corpus')
**A[u003]:** The provided documentation excerpts do not specify any information about the question asked.

## u004 · unanswerable
**Q:** What HNSW ef_construction value does Qdrant use by default?
_notes: vendor-internal detail not in LangChain docs_
> (unanswerable — expected behavior: decline / 'not in the corpus')
**A[u004]:** The provided documentation excerpts do not specify any information about the question asked.

## u005 · unanswerable
**Q:** What is Anthropic's rate limit for the claude-sonnet-4-6 API?
_notes: provider limits not documented in corpus_
> (unanswerable — expected behavior: decline / 'not in the corpus')
**A[u005]:** The provided documentation excerpts do not specify any information about the question asked.

## u006 · unanswerable
**Q:** When will LangGraph v2 be released?
_notes: future roadmap — corpus-gap_
> (unanswerable — expected behavior: decline / 'not in the corpus')
**A[u006]:** The provided documentation excerpts do not specify any information about the question asked.

## u007 · unanswerable
**Q:** What is the maximum number of subagents a deep agent can spawn?
_notes: no such hard limit documented — should say not stated_
> (unanswerable — expected behavior: decline / 'not in the corpus')
**A[u007]:** there is no built in maximum on the numner of subagents a deep agent can spawn.

## u008 · unanswerable
**Q:** How do I fine-tune an LLM using LangChain?
_notes: out of scope; LangChain doesn't do training_
> (unanswerable — expected behavior: decline / 'not in the corpus')
**A[u008]:** The provided documentation excerpts do not specify any information about the question asked.

## u009 · unanswerable
**Q:** What GPU is required to run LangGraph?
_notes: no hardware requirement documented — corpus-gap_
> (unanswerable — expected behavior: decline / 'not in the corpus')
**A[u009]:** The provided documentation excerpts do not specify any information about the question asked.

## u010 · unanswerable
**Q:** Who is the CEO of LangChain the company?
_notes: not covered in technical docs_
> (unanswerable — expected behavior: decline / 'not in the corpus')
**A[u010]:** The provided documentation excerpts do not specify the information about question asked.

## u011 · unanswerable
**Q:** What is the default embedding model used by the create_agent function?
_notes: false premise — create_agent has no embedding model; tests hallucination resistance_
> (unanswerable — expected behavior: decline / 'not in the corpus')
**A[u011]:** create_agent does not use or accept an embedding model

## u012 · unanswerable
**Q:** How do I configure Redis as a checkpointer with connection pooling and TLS?
_notes: specific vendor config likely beyond corpus — verify; may be partial corpus-gap_
> (unanswerable — expected behavior: decline / 'not in the corpus')
**A[u012]:** The provided documentation excerpts do not specify any information about the question asked.

## u013 · unanswerable
**Q:** What is the token cost per LangGraph node execution?
_notes: nodes don't have token cost — false-premise / corpus-gap_
> (unanswerable — expected behavior: decline / 'not in the corpus')
**A[u013]:** Nodes do not cost token.

## u014 · unanswerable
**Q:** How do I roll back a deployed LangGraph app to a previous version using the CLI?
_notes: verify against deploy.md; likely not documented — corpus-gap candidate_
> (unanswerable — expected behavior: decline / 'not in the corpus')
**A[u014]:** i can't, there is no instructions for rolling back a deployed LangGraph app using the cli.
