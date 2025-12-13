"""ARK OS - Main CLI Interface.

Beautiful terminal interface for ARK OS featuring:
- Rich terminal UI with colors, panels, and tables
- Direct agent interaction (no database required)
- Simple conversation context management
- Interactive commands for exploration
- API client mode for connecting to running servers

Run with:
    python base_module/main_interface.py              # Beautiful CLI (default)
    python base_module/main_interface.py --api        # API client mode
"""

import os
import sys
import uuid
import time
import argparse
from datetime import datetime
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

console = Console()


class ArkCLI:
    """Beautiful interactive ARK chat interface.
    
    Features:
    - Rich terminal UI with real-time feedback
    - Agent state tracking
    - Conversation context management
    - Performance monitoring
    """

    def __init__(self, llm_base_url: str = "http://localhost:30000/v1"):
        """Initialize ARK CLI.

        Args:
            llm_base_url: LLM base URL (default: http://localhost:30000/v1)
        """
        from agent_module.agent import Agent
        from state_module.state_handler import StateHandler
        from model_module.ArkModelNew import ArkModelLink, UserMessage, SystemMessage, AIMessage
        
        # Store message classes for later use
        self.UserMessage = UserMessage
        self.SystemMessage = SystemMessage
        self.AIMessage = AIMessage
        
        self.console = console
        self.agent_id = f"ark-agent-{uuid.uuid4().hex[:8]}"

        # Resolve state graph path
        script_dir = os.path.dirname(os.path.abspath(__file__))
        state_graph_path = os.path.join(
            os.path.dirname(script_dir),
            "state_module",
            "state_graph.yaml"
        )

        # Initialize components with beautiful progress display
        self.console.print("\n[bold cyan]╔════════════════════════════════════╗[/bold cyan]")
        self.console.print("[bold cyan]║     Initializing ARK OS...        ║[/bold cyan]")
        self.console.print("[bold cyan]╚════════════════════════════════════╝[/bold cyan]\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task1 = progress.add_task("[cyan]Loading state handler...", total=None)
            self.flow = StateHandler(yaml_path=state_graph_path)
            progress.update(task1, completed=True)

            task2 = progress.add_task("[cyan]Connecting to LLM...", total=None)
            self.llm = ArkModelLink(base_url=llm_base_url)
            progress.update(task2, completed=True)

            task3 = progress.add_task("[cyan]Initializing agent...", total=None)
            # Simple memory stub for future feature
            class SimpleMemoryStub:
                def __init__(self, agent_id: str):
                    self.agent_id = agent_id
            
            memory_stub = SimpleMemoryStub(agent_id=self.agent_id)
            
            self.agent = Agent(
                agent_id=self.agent_id,
                flow=self.flow,
                memory=memory_stub,
                llm=self.llm
            )
            progress.update(task3, completed=True)

        # Set initial system prompt
        self.system_prompt = """You are ARK, a helpful AI assistant.
Respond naturally to user messages and use tools when needed.
Always stay in character as ARK when responding."""

        self.agent.context["messages"] = [
            SystemMessage(content=self.system_prompt)
        ]

        # Statistics
        self.messages_sent = 0
        self.total_response_time = 0.0
        self.session_start = datetime.now()

        self.console.print("[bold green]✓ ARK OS initialized successfully![/bold green]\n")

    def show_header(self):
        """Display welcome header with instructions."""
        header = Panel(
            """[bold cyan]ARK OS - Interactive AI Assistant[/bold cyan]

[yellow]Commands:[/yellow]
  [bold]/help[/bold]      - Show this help message
  [bold]/context[/bold]   - View conversation history
  [bold]/stats[/bold]     - Show session statistics
  [bold]/clear[/bold]     - Clear conversation and start fresh
  [bold]/exit[/bold]      - Exit ARK

[green]Chat:[/green]
  Just type your message and press Enter to talk with ARK.
  All messages are kept in context for the conversation.

[dim]Memory features (PostgreSQL/mem0ai) are disabled for simplicity.
This will be added as a future feature.[/dim]
""",
            title="🚀 Welcome to ARK OS",
            border_style="cyan",
            expand=False
        )
        self.console.print(header)
        self.console.print(f"[dim]Agent ID: {self.agent_id}[/dim]\n")

    def process_message(self, message: str):
        """Process user message through agent.

        Args:
            message: User message
        """
        self.messages_sent += 1

        # Show user message in a nice panel
        self.console.print(Panel(
            f"[white]{message}[/white]",
            title="[bold cyan]You[/bold cyan]",
            border_style="cyan",
            expand=False
        ))

        # Add message to agent context
        self.agent.context["messages"].append(self.UserMessage(content=message))

        # Run agent step with spinner
        start_time = time.time()
        try:
            with self.console.status("[bold green]🤔 Agent thinking...", spinner="dots"):
                response = self.agent.step()

            elapsed = time.time() - start_time
            self.total_response_time += elapsed

            if response:
                # Add response to context
                self.agent.context["messages"].append(response)
                
                # Display response in a beautiful panel
                self.console.print(Panel(
                    f"[white]{response.content}[/white]",
                    title="[bold green]ARK[/bold green]",
                    border_style="green",
                    expand=False
                ))
                self.console.print(f"[dim]⏱️  Response time: {elapsed:.2f}s[/dim]\n")
            else:
                self.console.print("[yellow]⚠️  No response from agent[/yellow]\n")

        except Exception as e:
            self.console.print(Panel(
                f"[red]{str(e)}[/red]",
                title="[bold red]❌ Error[/bold red]",
                border_style="red"
            ))
            import traceback
            traceback.print_exc()

    def show_context(self):
        """Show current conversation context."""
        messages = self.agent.context.get("messages", [])
        
        if len(messages) <= 1:  # Only system message
            self.console.print("[yellow]No conversation yet - start chatting![/yellow]\n")
            return

        # Create a beautiful table
        context_table = Table(
            title="💬 Conversation History",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold magenta"
        )
        context_table.add_column("#", style="cyan", width=4, justify="right")
        context_table.add_column("Role", style="magenta", width=10)
        context_table.add_column("Message", style="white")

        for i, msg in enumerate(messages[1:], 1):  # Skip system message
            role = msg.__class__.__name__.replace("Message", "")
            content = msg.content
            
            # Truncate long messages
            if len(content) > 100:
                content = content[:97] + "..."
            
            # Color code by role
            role_emoji = "👤" if role == "User" else "🤖"
            context_table.add_row(
                str(i),
                f"{role_emoji} {role}",
                content
            )

        self.console.print(context_table)
        self.console.print(f"\n[dim]Total messages: {len(messages) - 1} (excluding system)[/dim]\n")

    def show_statistics(self):
        """Display session statistics."""
        session_duration = (datetime.now() - self.session_start).total_seconds()
        avg_response_time = (
            self.total_response_time / self.messages_sent
            if self.messages_sent > 0
            else 0
        )

        stats_panel = Panel(
            f"""[bold cyan]📊 Session Statistics[/bold cyan]

[yellow]Activity:[/yellow]
  Messages Sent:       {self.messages_sent}
  Session Duration:    {session_duration / 60:.1f} minutes
  Session Started:     {self.session_start.strftime("%H:%M:%S")}

[yellow]Performance:[/yellow]
  Avg Response Time:   {avg_response_time:.2f}s
  Total Response Time: {self.total_response_time:.2f}s

[yellow]Agent Info:[/yellow]
  Agent ID:            {self.agent_id}
  Messages in Context: {len(self.agent.context.get('messages', [])) - 1}
  Current State:       {self.agent.current_state.name if self.agent.current_state else 'N/A'}
""",
            title="Statistics",
            border_style="cyan"
        )
        self.console.print(stats_panel)

    def clear_context(self):
        """Clear conversation and start fresh."""
        self.agent.context["messages"] = [
            self.SystemMessage(content=self.system_prompt)
        ]
        self.messages_sent = 0
        self.total_response_time = 0.0
        self.session_start = datetime.now()
        
        self.console.print(Panel(
            "[green]✓ Conversation cleared - starting fresh![/green]",
            border_style="green"
        ))

    def run(self):
        """Run the interactive CLI."""
        self.show_header()

        while True:
            try:
                # Get user input with Rich prompt
                user_input = Prompt.ask("\n[bold cyan]You[/bold cyan]").strip()

                if not user_input:
                    continue

                # Handle commands
                if user_input.startswith("/"):
                    command = user_input[1:].lower()

                    if command in ["exit", "quit"]:
                        self.console.print("\n[bold green]👋 Goodbye! Thanks for using ARK OS.[/bold green]\n")
                        break

                    elif command == "help":
                        self.show_header()

                    elif command == "context":
                        self.show_context()

                    elif command == "stats":
                        self.show_statistics()

                    elif command == "clear":
                        self.clear_context()

                    else:
                        self.console.print(f"[yellow]❓ Unknown command: /{command}[/yellow]")
                        self.console.print("[dim]Type /help for available commands[/dim]\n")

                else:
                    # Process as chat message
                    self.process_message(user_input)

            except KeyboardInterrupt:
                self.console.print("\n\n[bold green]👋 Goodbye! Thanks for using ARK OS.[/bold green]\n")
                break

            except Exception as e:
                self.console.print(f"\n[red]Error: {e}[/red]\n")
                import traceback
                traceback.print_exc()


def run_api_client_mode(api_url: str = "http://localhost:1111/v1"):
    """Run in API client mode - connects to running API server.
    
    Args:
        api_url: URL of the ARK OS API server
    """
    from openai import OpenAI

    console.print("\n[bold cyan]╔════════════════════════════════════╗[/bold cyan]")
    console.print("[bold cyan]║     ARK OS - API Client Mode      ║[/bold cyan]")
    console.print("[bold cyan]╚════════════════════════════════════╝[/bold cyan]\n")
    
    console.print(f"[cyan]Connecting to API server at {api_url}...[/cyan]")

    try:
        client = OpenAI(base_url=api_url, api_key="not-needed")

        console.print("[bold green]✓ Connected![/bold green]\n")
        console.print("[dim]Type /exit to quit, or just chat with ARK[/dim]\n")

        # Main interaction loop with Rich
        while True:
            user_input = Prompt.ask("\n[bold cyan]You[/bold cyan]").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ["/exit", "/quit", "exit", "quit"]:
                console.print("\n[bold green]👋 Goodbye![/bold green]\n")
                break

            try:
                with console.status("[bold green]🤔 Agent thinking...", spinner="dots"):
                    response = client.chat.completions.create(
                        model="ark-agent",
                        messages=[{"role": "user", "content": user_input}]
                    )
                
                message = response.choices[0].message.content
                
                console.print(Panel(
                    f"[white]{message}[/white]",
                    title="[bold green]ARK[/bold green]",
                    border_style="green",
                    expand=False
                ))

            except Exception as e:
                console.print(Panel(
                    f"[red]{str(e)}[/red]\n\n[yellow]Make sure the API server is running:[/yellow]\n[cyan]python base_module/app.py[/cyan]",
                    title="[bold red]❌ Connection Error[/bold red]",
                    border_style="red"
                ))

    except Exception as e:
        console.print(Panel(
            f"[red]{str(e)}[/red]\n\n[yellow]Make sure:[/yellow]\n1. The API server is running: [cyan]python base_module/app.py[/cyan]\n2. The server is accessible at {api_url}",
            title="[bold red]❌ Connection Error[/bold red]",
            border_style="red"
        ))


def main():
    """Main entry point with mode selection."""
    parser = argparse.ArgumentParser(
        description="ARK OS - Beautiful CLI Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python base_module/main_interface.py                    # Beautiful CLI (default)
  python base_module/main_interface.py --api              # API client mode
  python base_module/main_interface.py --llm-url http://localhost:30000/v1
        """
    )
    
    parser.add_argument(
        "--api",
        action="store_true",
        help="Use API client mode instead of direct agent mode"
    )
    parser.add_argument(
        "--api-url",
        type=str,
        default="http://localhost:1111/v1",
        help="API server URL for API client mode (default: http://localhost:1111/v1)"
    )
    parser.add_argument(
        "--llm-url",
        type=str,
        default="http://localhost:30000/v1",
        help="LLM server URL for direct agent mode (default: http://localhost:30000/v1)"
    )

    args = parser.parse_args()

    try:
        if args.api:
            run_api_client_mode(api_url=args.api_url)
        else:
            cli = ArkCLI(llm_base_url=args.llm_url)
            cli.run()
    except KeyboardInterrupt:
        console.print("\n\n[bold green]👋 Goodbye![/bold green]\n")
    except Exception as e:
        console.print(Panel(
            f"[red]{str(e)}[/red]\n\n[yellow]Make sure:[/yellow]\n1. The LLM server is running on port 30000\n2. The state_graph.yaml file exists",
            title="[bold red]❌ Fatal Error[/bold red]",
            border_style="red"
        ))
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

