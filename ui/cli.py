# Não esquecer de executar o venv\Services\activate
# para poder testar o código rodando no terminal


from __future__ import annotations

import re
from datetime import date

from rich.console import Console
from rich.prompt import Prompt, IntPrompt
from rich.table import Table
from rich.panel import Panel

from services.data_service import load_data, save_data


console = Console()

def normalize_slug(value: str) -> str:
    """
    Minimal slug normalization, so things won't get messed up.
    - lowercases
    - spaces/underscores to hyphen
    - removes invalid chars
    """
    value = value.strip().lower()
    value = value.replace("_", "-")
    value = re.sub(r"\s+", "-", value)
    value = re.sub(r"[^a-z0-9-]", "", value)
    value = re.sub(r"-{2,}", "-", value).strip("-")
    return value

def pause(message: str | None = None) -> None:
    """
    This function displays a message and prompts the user to press ENTER to continue.
  
    The `message` parameter is a string that represents a message to be displayed before
    prompting the user to press ENTER to continue. It is optional and can be set to `None`
    (set as a default value) if no message needs to be displayed.
    """
    if message:
        console.print(f"\n{message}")
    Prompt.ask("\nPress ENTER to continue", default="")

def add_habit_flow() -> None:
    # This function adds a new habit to the data.
    data = load_data()

    console.clear()
    console.print(Panel.fit("[bold]Add Habit[/bold]"))

    def input_habit_name() -> str:
      # this function requests the habit name and validates it.
      while True:
          name = Prompt.ask("Habit name").strip()
          if name:
              return name
          pause("Name cannot be empty.")
    
    name = input_habit_name()

    def input_habit_id() -> str:
      # this function requests the habit id and validates it.
      # It checks not only if it is empty, but if the ID already exists.
      # May modify later...
      existing_ids = {h.get("id") for h in data["habits"]}

      while True:
          habit_id = Prompt.ask("Habit ID (slug, e.g. 'drink-water')").strip().lower()
          habit_id = normalize_slug(habit_id)
          
          if not habit_id:
            pause("Habit ID cannot be empty.")
            continue
          if habit_id in existing_ids:
            pause(f"Habit ID '{habit_id}' already exists.")
            continue

          return habit_id
    
    habit_id = input_habit_id()
    # habit_id = normalize_slug(habit_id)

    def input_habit_unit() -> str:
      # this function requests the habit unit and... validates... it.
      while True:
          unit = Prompt.ask("Unit (e.g. 'minutes', 'cups', 'sessions')", default="times").strip()
          if unit:
              return unit
          pause("Unit cannot be empty.")

    unit = input_habit_unit()

    target = IntPrompt.ask("Target per day", default=1)

    habit = {
        "id": habit_id,
        "name": name,
        "unit": unit,
        "target_per_day": int(target),
        "created_at": date.today().isoformat(),
    }

    data["habits"].append(habit)
    save_data(data)

    pause(f"Habit '{name}' added successfully.")

def list_habits_flow() -> None:
    # This function lists all the habits in a nice manner using rich.
    data = load_data()

    console.clear()
    console.print(Panel.fit("[bold]Habits[/bold]"))

    table = Table(show_header=True, header_style="bold")
    table.add_column("ID", style="dim", no_wrap=True)
    table.add_column("Name")
    table.add_column("Unit")
    table.add_column("Target/Day", justify="right")
    table.add_column("Created", style="dim", no_wrap=True)

    for h in data["habits"]:
        table.add_row(
            str(h.get("id", "")),
            str(h.get("name", "")),
            str(h.get("unit", "")),
            str(h.get("target_per_day", "")),
            str(h.get("created_at", "")),
        )

    if not data["habits"]:
        console.print("[dim]No habits registered yet.[/dim]")
    else:
        console.print(table)

    pause()

def start_app() -> None:
    while True:
        # creating the main menu of the application
        # using rich to properly format it
        console.clear()
        console.print(Panel.fit("[bold]Habit Tracker Dashboard[/bold]", subtitle="CLI MVP"))

        # Options menu.
        console.print("\nWhat would you like to do?")
        console.print("1) Add habit")
        console.print("2) List habits")
        console.print("3) Exit")

        choice = Prompt.ask("\nChoose an option", choices=["1", "2", "3"], default="2")

        if choice == "1":
            add_habit_flow()
        elif choice == "2":
            list_habits_flow()
        else:
            console.print("\nGoodbye.")
            break





