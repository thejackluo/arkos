"""Interactive ARK REPL with Real-Time Memory and Agent Visualization.

This is the enhanced CLI interface for ARK OS featuring:
- Rich terminal UI with real-time feedback
- Memory operation visualization
- Agent state tracking
- Command system for exploration
- Statistics and monitoring

Run with:
    python base_module/ark_repl.py
"""

import os
import sys
import uuid
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.live import Live
from rich.layout import Layout
from rich.text import Text
from rich import box
from rich.progress import Progress, SpinnerColumn, TextColumn

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from agent_module.agent import Agent
from state_module.state_handler import StateHandler
from memory_module.memory import Memory
from model_module.ArkModelNew import ArkModelLink, UserMessage, SystemMessage, AIMessage


console = Console()


class ArkREPL:
    """Interactive ARK chat with real-time visualization.

    Features:
    - See agent state transitions in real-time
    - Visualize memory operations (add/retrieve)
    - Track conversation context
    - Monitor agent performance
    - Explore memories and sessions
    """

    def __init__(
        self,
        user_id: Optional[str] = None,
        db_url: str = "postgresql://postgres:your-super-secret-and-long-postgres-password@localhost:54322/postgres",
        llm_base_url: str = "http://localhost:30000/v1",
        state_graph_path: Optional[str] = None
    ):
        """Initialize ARK REPL.

        Args:
            user_id: User ID (generates new if not provided)
            db_url: PostgreSQL connection string
            llm_base_url: LLM base URL
            state_graph_path: Path to state graph YAML (auto-detected if not provided)
        """
        self.console = console
        self.user_id = user_id or f"ark-user-{uuid.uuid4().hex[:8]}"

        # Resolve state graph path if not provided
        if state_graph_path is None:
            # Get the directory where this script is located
            script_dir = os.path.dirname(os.path.abspath(__file__))
            # Go up one level to arkos root, then into state_module
            state_graph_path = os.path.join(
                os.path.dirname(script_dir),
                "state_module",
                "state_graph.yaml"
            )

        # Initialize components
        self.console.print("\n[bold cyan]Initializing ARK OS...[/bold cyan]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task1 = progress.add_task("[cyan]Loading state handler...", total=None)
            self.flow = StateHandler(yaml_path=state_graph_path)
            progress.update(task1, completed=True)

            task2 = progress.add_task("[cyan]Connecting to memory system...", total=None)
            self.memory = Memory(
                user_id=self.user_id,
                session_id=None,  # Will generate new session
                db_url=db_url
            )
            progress.update(task2, completed=True)

            task3 = progress.add_task("[cyan]Connecting to LLM...", total=None)
            self.llm = ArkModelLink(base_url=llm_base_url)
            progress.update(task3, completed=True)

            task4 = progress.add_task("[cyan]Initializing agent...", total=None)
            self.agent = Agent(
                agent_id=f"ark-agent-{uuid.uuid4().hex[:8]}",
                flow=self.flow,
                memory=self.memory,
                llm=self.llm
            )
            progress.update(task4, completed=True)

        # Set initial system prompt
        self.system_prompt = """You are ARK, a helpful AI assistant with memory and access to specific tools.
If the user request requires a tool, call the appropriate state.
Always stay in character as ARK when responding."""

        if "messages" not in self.agent.context:
            self.agent.context["messages"] = [
                SystemMessage(content=self.system_prompt)
            ]

        # Statistics
        self.messages_sent = 0
        self.memories_added = 0
        self.total_response_time = 0.0
        self.session_start_time = datetime.now()

        self.console.print("[bold green]ARK OS initialized successfully![/bold green]\n")

    def show_header(self):
        """Display welcome header with instructions."""
        header = Panel(
            """[bold cyan]ARK OS - Interactive Memory-Enabled Agent[/bold cyan]

[yellow]Commands:[/yellow]
  [bold]/search <query>[/bold]  - Search your memories
  [bold]/memories[/bold]        - List recent memories
  [bold]/stats[/bold]           - Show session statistics
  [bold]/context[/bold]         - View conversation context
  [bold]/newsession[/bold]      - Start a new session
  [bold]/help[/bold]            - Show this help
  [bold]/exit[/bold]            - Exit ARK

[green]Chat Features:[/green]
  - All messages are automatically stored in memory
  - Agent can access past conversations and context
  - Real-time visualization of agent operations
  - Memory-augmented responses using vector search
""",
            title="Welcome to ARK OS",
            border_style="cyan",
            expand=False
        )
        self.console.print(header)
        self.console.print(f"\n[dim]User ID: {self.user_id}[/dim]")
        self.console.print(f"[dim]Session ID: {self.memory.session_id}[/dim]\n")

    async def process_message(self, message: str):
        """Process user message through agent.

        Args:
            message: User message
        """
        self.messages_sent += 1

        # Show message
        self.console.print("\n" + "=" * 70)
        self.console.print(f"[bold cyan]You:[/bold cyan] {message}")
        self.console.print("=" * 70)

        # Step 1: Store in memory
        self.console.print("\n[yellow]1. Storing in Memory...[/yellow]")
        try:
            success = self.memory.add_memory(message, role="user")
            if success:
                self.memories_added += 1
                self.console.print("[green]  Memory stored successfully[/green]")
            else:
                self.console.print("[red]  Failed to store memory[/red]")
        except Exception as e:
            self.console.print(f"[red]  Error storing memory: {e}[/red]")

        # Step 2: Retrieve relevant context
        self.console.print("\n[yellow]2. Retrieving Relevant Context...[/yellow]")
        try:
            context_data = self.memory.retrieve_memory(query=message, mem0_limit=5)

            if "retrieved_memories" in context_data and context_data["retrieved_memories"]:
                context_table = Table(title="Retrieved Memories", box=box.SIMPLE)
                context_table.add_column("#", style="cyan", width=3)
                context_table.add_column("Memory", style="white")

                for i, mem in enumerate(context_data["retrieved_memories"][:5], 1):
                    context_table.add_row(str(i), mem[:70] + ("..." if len(mem) > 70 else ""))

                self.console.print(context_table)
            else:
                self.console.print("[dim]  No relevant memories found[/dim]")
        except Exception as e:
            self.console.print(f"[red]  Error retrieving context: {e}[/red]")

        # Step 3: Add message to agent context
        self.console.print("\n[yellow]3. Processing with Agent...[/yellow]")
        self.agent.context["messages"].append(UserMessage(content=message))

        # Step 4: Run agent step
        start_time = time.time()
        try:
            with self.console.status("[bold green]Agent thinking...", spinner="dots"):
                response = self.agent.step()

            elapsed = time.time() - start_time
            self.total_response_time += elapsed

            if response:
                # Store assistant response in memory
                try:
                    self.memory.add_memory(response.content, role="assistant")
                    self.memories_added += 1
                except:
                    pass

                # Display response
                self.console.print("\n[bold green]ARK:[/bold green]")
                response_panel = Panel(
                    response.content,
                    border_style="green",
                    expand=False
                )
                self.console.print(response_panel)
                self.console.print(f"\n[dim]Response time: {elapsed:.2f}s[/dim]")
            else:
                self.console.print("\n[yellow]No response from agent[/yellow]")

        except Exception as e:
            self.console.print(f"\n[red]Agent error: {e}[/red]")
            import traceback
            traceback.print_exc()

    def search_memories(self, query: str):
        """Search memories and display results.

        Args:
            query: Search query
        """
        self.console.print(f"\n[cyan]Searching for: \"{query}\"[/cyan]\n")

        try:
            results = self.memory.retrieve_memory(query=query, mem0_limit=10)

            if "retrieved_memories" in results and results["retrieved_memories"]:
                results_table = Table(title="Search Results", box=box.ROUNDED)
                results_table.add_column("#", style="cyan", width=4)
                results_table.add_column("Memory", style="white")

                for i, mem in enumerate(results["retrieved_memories"], 1):
                    results_table.add_row(str(i), mem)

                self.console.print(results_table)
                self.console.print(f"\n[green]Found {len(results['retrieved_memories'])} results[/green]")
            else:
                self.console.print("[yellow]No results found[/yellow]")

        except Exception as e:
            self.console.print(f"[red]Search error: {e}[/red]")

    def show_recent_memories(self):
        """Display recent conversation history."""
        self.console.print("\n[cyan]Recent Conversation History[/cyan]\n")

        try:
            context_data = self.memory.retrieve_memory(query="", mem0_limit=20)

            if "conversation_ctx" in context_data and context_data["conversation_ctx"]:
                lines = context_data["conversation_ctx"].split("\n")

                memory_table = Table(title="Conversation History", box=box.ROUNDED)
                memory_table.add_column("Role", style="magenta", width=10)
                memory_table.add_column("Message", style="white")

                for line in lines[-20:]:  # Last 20 messages
                    if ":" in line:
                        role, msg = line.split(":", 1)
                        memory_table.add_row(role.strip(), msg.strip())

                self.console.print(memory_table)
            else:
                self.console.print("[dim]No conversation history yet[/dim]")

        except Exception as e:
            self.console.print(f"[red]Error retrieving memories: {e}[/red]")

    def show_context(self):
        """Show current agent context."""
        self.console.print("\n[cyan]Current Agent Context[/cyan]\n")

        if "messages" in self.agent.context:
            context_table = Table(title="Agent Message Context", box=box.ROUNDED)
            context_table.add_column("#", style="cyan", width=4)
            context_table.add_column("Role", style="magenta", width=10)
            context_table.add_column("Content", style="white")

            for i, msg in enumerate(self.agent.context["messages"][-10:], 1):
                role = msg.__class__.__name__.replace("Message", "").lower()
                content = msg.content[:60] + ("..." if len(msg.content) > 60 else "")
                context_table.add_row(str(i), role, content)

            self.console.print(context_table)
            self.console.print(f"\n[dim]Total messages in context: {len(self.agent.context['messages'])}[/dim]")
        else:
            self.console.print("[yellow]No context available[/yellow]")

    def show_statistics(self):
        """Display session statistics."""
        session_duration = (datetime.now() - self.session_start_time).total_seconds()
        avg_response_time = (
            self.total_response_time / self.messages_sent
            if self.messages_sent > 0
            else 0
        )

        stats_panel = Panel(
            f"""[bold cyan]Session Statistics[/bold cyan]

[yellow]Activity:[/yellow]
  Messages Sent:       {self.messages_sent}
  Memories Stored:     {self.memories_added}
  Session Duration:    {session_duration / 60:.1f} minutes

[yellow]Performance:[/yellow]
  Avg Response Time:   {avg_response_time:.2f}s
  Total Response Time: {self.total_response_time:.2f}s

[yellow]Session Info:[/yellow]
  User ID:            {self.user_id}
  Session ID:         {self.memory.session_id}
  Agent ID:           {self.agent.agent_id}

[yellow]Agent Context:[/yellow]
  Messages in Context: {len(self.agent.context.get('messages', []))}
""",
            title="Statistics",
            border_style="cyan"
        )

        self.console.print(stats_panel)

    def new_session(self):
        """Start a new chat session."""
        old_session = self.memory.session_id
        new_session = self.memory.start_new_session()

        self.console.print(f"\n[green]Started new session![/green]")
        self.console.print(f"[dim]Old session: {old_session}[/dim]")
        self.console.print(f"[dim]New session: {new_session}[/dim]\n")

        # Reset agent context
        self.agent.context["messages"] = [
            SystemMessage(content=self.system_prompt)
        ]

    def run(self):
        """Run the interactive REPL."""
        self.show_header()

        while True:
            try:
                # Get user input
                user_input = self.console.input("\n[bold cyan]You:[/bold cyan] ").strip()

                if not user_input:
                    continue

                # Handle commands
                if user_input.startswith("/"):
                    command = user_input[1:].lower()

                    if command == "exit" or command == "quit":
                        self.console.print("\n[bold]Goodbye! Your memories are saved.[/bold]\n")
                        break

                    elif command == "help":
                        self.show_header()

                    elif command == "stats":
                        self.show_statistics()

                    elif command == "memories":
                        self.show_recent_memories()

                    elif command == "context":
                        self.show_context()

                    elif command == "newsession":
                        self.new_session()

                    elif command.startswith("search "):
                        query = command[7:].strip()
                        if query:
                            self.search_memories(query)
                        else:
                            self.console.print("[yellow]Usage: /search <query>[/yellow]")

                    else:
                        self.console.print(f"[yellow]Unknown command: /{command}[/yellow]")
                        self.console.print("[dim]Type /help for available commands[/dim]")

                else:
                    # Process as chat message - note: using sync wrapper for async method
                    import asyncio
                    asyncio.run(self.process_message(user_input))

            except KeyboardInterrupt:
                self.console.print("\n\n[bold]Goodbye! Your memories are saved.[/bold]\n")
                break

            except Exception as e:
                self.console.print(f"\n[red]Error: {e}[/red]")
                import traceback
                traceback.print_exc()


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="ARK OS Interactive REPL")
    parser.add_argument("--user-id", type=str, help="User ID (generates new if not provided)")
    parser.add_argument(
        "--db-url",
        type=str,
        default="postgresql://postgres:your-super-secret-and-long-postgres-password@localhost:54322/postgres",
        help="PostgreSQL connection string"
    )
    parser.add_argument(
        "--llm-url",
        type=str,
        default="http://localhost:30000/v1",
        help="LLM base URL"
    )
    parser.add_argument(
        "--state-graph",
        type=str,
        default=None,
        help="Path to state graph YAML (auto-detected if not provided)"
    )

    args = parser.parse_args()

    try:
        repl = ArkREPL(
            user_id=args.user_id,
            db_url=args.db_url,
            llm_base_url=args.llm_url,
            state_graph_path=args.state_graph
        )
        repl.run()
    except KeyboardInterrupt:
        console.print("\n\n[bold]Goodbye![/bold]\n")
    except Exception as e:
        console.print(f"\n[red]Fatal error: {e}[/red]\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
