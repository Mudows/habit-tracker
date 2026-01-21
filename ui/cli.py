from __future__ import annotations

import re
from datetime import date

from typing import Any, Dict

from rich.console import Console
from rich.prompt import Prompt, IntPrompt
from rich.table import Table
from rich.panel import Panel

from services.data_service import load_data, save_data
from services.sparkline import sparkline
from services.stats import entries_for_habit, totals_by_day, streak_days_meeting_target, weekly_total, monthly_total, last_n_days_values


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


def choose_habit(data: Dict[str, Any]) -> Dict[str, Any] | None:
    habits = data.get("habits", [])
    if not habits:
        pause("No habits found.")
        return None

    table = Table(show_header=True, header_style="bold")
    table.add_column("#", justify="right", style="dim", no_wrap=True)
    table.add_column("ID", style="dim", no_wrap=True)
    table.add_column("Name")
    table.add_column("Unit")
    table.add_column("Target/Day", justify="right")

    for i, h in enumerate(habits, start=1):
        table.add_row(
            str(i),
            str(h.get("id", "")),
            str(h.get("name", "")),
            str(h.get("unit", "")),
            str(h.get("target_per_day", "")),
        )

    console.print(table)

    idx = IntPrompt.ask("\nChoose a habit number", default=1)
    if idx < 1 or idx > len(habits):
        pause("Invalid selection.")
        return None

    return habits[idx - 1]

def edit_habit_flow() -> None:
    data = load_data()

    console.clear()
    console.print(Panel.fit("[bold]Edit Habit[/bold]"))

    habit = choose_habit(data)
    if not habit:
        return

    console.print("\n[dim]Leave blank to keep current value.[/dim]")

    current_name = str(habit.get("name", ""))
    current_unit = str(habit.get("unit", "times"))
    current_target = int(habit.get("target_per_day", 1))

    new_name = Prompt.ask("Name", default=current_name).strip()
    new_unit = Prompt.ask("Unit", default=current_unit).strip()

    # Target: permitir ENTER mantendo atual
    raw_target = Prompt.ask("Target per day", default=str(current_target)).strip()
    try:
        new_target = int(raw_target)
        if new_target < 0:
            raise ValueError
    except ValueError:
        pause("Invalid target. Must be a non-negative integer.")
        return

    habit["name"] = new_name if new_name else current_name
    habit["unit"] = new_unit if new_unit else current_unit
    habit["target_per_day"] = new_target

    save_data(data)
    pause("Habit updated successfully.")

def remove_habit_flow() -> None:
    data = load_data()

    console.clear()
    console.print(Panel.fit("[bold]Delete Habit[/bold]"))

    habit = choose_habit(data)
    if not habit:
        return

    hid = habit.get("id", "")
    name = habit.get("name", hid)

    console.print(f"\nYou are about to delete: [bold]{name}[/bold] ([dim]{hid}[/dim])")
    confirm = Prompt.ask("Type DELETE to confirm", default="").strip()

    if confirm != "DELETE":
        pause("Deletion cancelled.")
        return

    # o que fazer com entries?
    console.print("\nWhat should happen to existing entries for this habit?")
    console.print("1) Delete habit only (keep entries)")
    console.print("2) Delete habit + delete associated entries (recommended)")

    mode = Prompt.ask("Choose", choices=["1", "2"], default="2")

    # Remove habit
    data["habits"] = [h for h in data.get("habits", []) if h.get("id") != hid]

    if mode == "2":
        data["entries"] = [e for e in data.get("entries", []) if e.get("habit_id") != hid]

    save_data(data)
    pause("Habit deleted successfully.")


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


def log_today_flow() -> None:
    data = load_data()
    habits = data.get("habits", [])

    console.clear()
    console.print(Panel.fit("[bold]Log Habit Entry[/bold]", subtitle="Today"))

    if not habits:
        pause("No habits found. Create a habit first.")
        return

    # Tabela para o usuário escolher
    table = Table(show_header=True, header_style="bold")
    table.add_column("#", justify="right", style="dim", no_wrap=True)
    table.add_column("ID", style="dim", no_wrap=True)
    table.add_column("Name")
    table.add_column("Unit")
    table.add_column("Target/Day", justify="right")

    for i, h in enumerate(habits, start=1):
        table.add_row(
            str(i),
            str(h.get("id", "")),
            str(h.get("name", "")),
            str(h.get("unit", "")),
            str(h.get("target_per_day", "")),
        )

    console.print(table)

    idx = IntPrompt.ask("\nChoose a habit number", default=1)
    if idx < 1 or idx > len(habits):
        pause("Invalid selection.")
        return

    habit = habits[idx - 1]
    habit_id = habit["id"]

    today = date.today().isoformat()
    value = IntPrompt.ask(f"Value for today ({habit.get('unit','times')})", default=1)
    note = Prompt.ask("Note (optional)", default="").strip()

    entry = {
        "date": today,
        "habit_id": habit_id,
        "value": int(value),
        "note": note,
    }

    entries = data.setdefault("entries", [])
    today = entry["date"]
    hid = entry["habit_id"]

    existing = next((e for e in entries if e.get("date") == today and e.get("habit_id") == hid), None)

    if existing:
        existing["value"] = entry["value"]
        existing["note"] = entry.get("note", "")
        action = "updated"
    else:
        entries.append(entry)
        action = "created"

    save_data(data)
    pause(f"Entry {action}: {habit.get('name')} = {entry['value']} on {today}.")


    # pause(f"Entry saved: {habit.get('name')} = {value} on {today}.")

def list_entries_flow() -> None:
    data = load_data()
    entries = data.get("entries", [])
    habits = {h["id"]: h for h in data.get("habits", [])}

    console.clear()
    console.print(Panel.fit("[bold]Entries[/bold]"))

    if not entries:
        pause("No entries found.")
        return

    table = Table(show_header=True, header_style="bold")
    table.add_column("Date", style="dim", no_wrap=True)
    table.add_column("Habit")
    table.add_column("Value", justify="right")
    table.add_column("Note")

    # show recent entries first (by date).
    for e in sorted(entries, key=lambda x: x.get("date",""), reverse=True)[:50]:
        h = habits.get(e.get("habit_id", ""), {})
        habit_name = h.get("name", e.get("habit_id", ""))
        table.add_row(
            str(e.get("date","")),
            str(habit_name),
            str(e.get("value","")),
            str(e.get("note","")),
        )

    console.print(table)
    pause()


def stats_overview_flow() -> None:
    data = load_data()
    habits = data.get("habits", [])

    console.clear()
    console.print(Panel.fit("[bold]Stats Overview[/bold]"))

    if not habits:
        pause("No habits found.")
        return

    table = Table(show_header=True, header_style="bold")
    table.add_column("Habit")
    table.add_column("Last 7d", justify="right")
    table.add_column("Last 30d", justify="right")
    table.add_column("Streak (days)", justify="right")

    for h in habits:
        hid = h["id"]
        target = int(h.get("target_per_day", 1))

        ent = entries_for_habit(data, hid)
        totals = totals_by_day(ent)

        wk = weekly_total(totals)
        mo = monthly_total(totals)
        streak = streak_days_meeting_target(totals, target)

        table.add_row(
            str(h.get("name", hid)),
            str(wk),
            str(mo),
            str(streak),
        )

    console.print(table)
    pause()


def habit_details_flow() -> None:
    data = load_data()
    habits = data.get("habits", [])

    console.clear()
    console.print(Panel.fit("[bold]Habit Details[/bold]"))

    if not habits:
        pause("No habits found.")
        return

    table = Table(show_header=True, header_style="bold")
    table.add_column("#", justify="right", style="dim", no_wrap=True)
    table.add_column("ID", style="dim", no_wrap=True)
    table.add_column("Name")

    for i, h in enumerate(habits, start=1):
        table.add_row(str(i), str(h.get("id","")), str(h.get("name","")))

    console.print(table)

    idx = IntPrompt.ask("\nChoose a habit number", default=1)
    if idx < 1 or idx > len(habits):
        pause("Invalid selection.")
        return

    h = habits[idx - 1]
    hid = h["id"]
    target = int(h.get("target_per_day", 1))

    ent = entries_for_habit(data, hid)
    totals = totals_by_day(ent)

    wk = weekly_total(totals)
    mo = monthly_total(totals)
    streak = streak_days_meeting_target(totals, target)
    vals14 = last_n_days_values(totals, 14)
    chart = sparkline(vals14)

    console.clear()
    console.print(Panel.fit(f"[bold]{h.get('name', hid)}[/bold]  [dim]({hid})[/dim]"))
    console.print(f"Target/day: {target} {h.get('unit','times')}")
    console.print(f"Last 7 days: {wk}")
    console.print(f"Last 30 days: {mo}")
    console.print(f"Streak: {streak} day(s)")
    console.print(f"\nLast 14 days: {chart}")
    console.print(f"[dim]{' '.join(str(v).rjust(2) for v in vals14)}[/dim]")

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
        console.print("3) Edit habit")
        console.print("4) Remove habit")
        console.print("5) Log habit entry (today)")
        console.print("6) List entries")
        console.print("7) Stats overview")
        console.print("8) Habits details")
        console.print("9) Exit")

        choice = Prompt.ask("\nChoose an option", choices=[str(i) for i in range(1, 10)], default="2")

        if choice == "1":
            add_habit_flow()
        elif choice == "2":
            list_habits_flow()
        elif choice == "3":
            edit_habit_flow()
        elif choice == "4":
            remove_habit_flow()
        elif choice == "5":
            log_today_flow()
        elif choice == "6":
            list_entries_flow()
        elif choice == "7":
            stats_overview_flow()
        elif choice == "8":
            habit_details_flow()
        else:
            console.print("\nGoodbye!")
            break



