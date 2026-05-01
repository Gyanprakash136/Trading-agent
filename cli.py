import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from dotenv import load_dotenv

from bot.orders import execute_trade
from bot.validators import validate_order_type_and_price, validate_side, validate_quantity
from bot.huggingface_client import MarketSentimentAnalyzer, HFAnalyzerError
from bot.logging_config import logger

# Load environment variables
load_dotenv()

app = typer.Typer(help="Binance Futures Testnet Trading Bot CLI")
console = Console()

def _display_and_execute_trade(symbol: str, side: str, order_type: str, quantity: float, price: float = None):
    # Validation
    try:
        validate_side(side)
        validate_order_type_and_price(order_type, price)
        validate_quantity(quantity)
    except ValueError as e:
        console.print(f"[bold red]Validation Error:[/bold red] {e}")
        logger.warning(f"Validation Error: {e}")
        raise typer.Exit(code=1)

    # Summary display
    price_str = f" at {price}" if price else ""
    console.print(Panel(
        f"Placing [bold cyan]{order_type}[/bold cyan] order to [bold green]{side}[/bold green] "
        f"[bold yellow]{quantity}[/bold yellow] of [bold magenta]{symbol}[/bold magenta]{price_str}", 
        title="Order Request Summary"
    ))
    
    # Execution
    try:
        response = execute_trade(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=quantity,
            price=price
        )
        
        # Output response details
        table = Table(title="Order Response Details", show_header=True, header_style="bold green")
        table.add_column("Key", style="cyan")
        table.add_column("Value", style="magenta")
        
        keys_to_show = ["orderId", "status", "symbol", "side", "type", "executedQty", "avgPrice", "clientOrderId"]
        for k in keys_to_show:
            if k in response:
                table.add_row(k, str(response[k]))
                
        console.print(table)
        console.print("[bold green]✅ Order placed successfully![/bold green]")
        
    except Exception as e:
        console.print(f"[bold red]❌ Failed to place order:[/bold red] {e}")
        raise typer.Exit(code=1)

@app.command("trade")
def trade(
    symbol: str = typer.Argument(..., help="Trading symbol, e.g., BTCUSDT"),
    side: str = typer.Argument(..., help="BUY or SELL"),
    order_type: str = typer.Argument(..., help="MARKET or LIMIT"),
    quantity: float = typer.Argument(..., help="Order quantity"),
    price: float = typer.Option(None, "--price", "-p", help="Order price (required for LIMIT orders)"),
):
    """Place a manual trade on the Binance Futures Testnet."""
    _display_and_execute_trade(symbol, side, order_type, quantity, price)

@app.command("interactive")
def interactive():
    """Interactive mode to place a trade with step-by-step prompts."""
    console.print("[bold cyan]🚀 Welcome to the Interactive Trading Bot[/bold cyan]")
    
    symbol = Prompt.ask("Enter trading symbol", default="BTCUSDT").upper()
    side = Prompt.ask("Enter side", choices=["BUY", "SELL"]).upper()
    order_type = Prompt.ask("Enter order type", choices=["MARKET", "LIMIT"]).upper()
    quantity = float(Prompt.ask("Enter quantity (e.g., 0.001)"))
    
    price = None
    if order_type == "LIMIT":
        price = float(Prompt.ask("Enter limit price"))
        
    if Confirm.ask(f"Execute {side} {quantity} {symbol} ({order_type})?"):
        _display_and_execute_trade(symbol, side, order_type, quantity, price)
    else:
        console.print("[yellow]Trade cancelled by user.[/yellow]")

@app.command("ai-trade")
def ai_trade(
    symbol: str = typer.Argument(..., help="Trading symbol, e.g., BTCUSDT"),
    quantity: float = typer.Argument(..., help="Order quantity to place if AI suggests a trade"),
    news_text: str = typer.Argument(..., help="News headline or context for AI analysis"),
):
    """Use Hugging Face AI to analyze a news headline and suggest/execute a trade."""
    console.print(Panel(f"Analyzing text:\n[italic]{news_text}[/italic]", title="🧠 AI Sentiment Analysis"))
    
    analyzer = MarketSentimentAnalyzer()
    try:
        with console.status("[bold green]Analyzing sentiment via Hugging Face...[/bold green]"):
            result = analyzer.analyze_sentiment(news_text)
            
        sentiment = result["sentiment"].upper()
        confidence = result["confidence"]
        signal = result["signal"]
        
        color = "green" if signal == "BUY" else "red" if signal == "SELL" else "yellow"
        
        console.print(f"Sentiment: [bold {color}]{sentiment}[/bold {color}]")
        console.print(f"Trading Signal: [bold {color}]{signal}[/bold {color}]")
        console.print(f"\n[bold]Agent Reasoning:[/bold]\n[italic]{result['reasoning']}[/italic]\n")
        
        if signal == "HOLD":
            console.print("[yellow]AI suggests HOLD. No trade executed.[/yellow]")
            return
            
        if Confirm.ask(f"Do you want to execute a MARKET {signal} order for {quantity} {symbol}?"):
            _display_and_execute_trade(symbol, signal, "MARKET", quantity, None)
        else:
            console.print("[yellow]Trade cancelled by user.[/yellow]")
            
    except HFAnalyzerError as e:
        console.print(f"[bold red]AI Analysis Failed:[/bold red] {e}")
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()
