# Não esquecer de executar o venv\Services\activate
# para poder testar o código rodando no terminal


from rich.console import Console
from services.data_service import load_data

console = Console()

def start_app():
  data = load_data()
  console.print("[bold red]Habit Tracker Dashboard[/bold red]")
  console.print("The App is running.")
  console.print(f"Habits: {len(data['habits'])} | Entries: {len(data['entries'])}")
