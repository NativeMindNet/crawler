#!/usr/bin/env python3
"""
SDD (Spec-Driven Development) Flow Command Handler

Usage:
    run sdd-crawler [command] [args]

Commands:
    start [name]     - Start new SDD flow
    resume [name]    - Resume existing flow
    fork [existing] [new] - Fork for context recovery
    status           - Show all active SDD flows
    help             - Show this help
"""

import os
import sys
import shutil
from datetime import datetime
from pathlib import Path

FLOWS_DIR = Path(__file__).parent.parent.parent / "flows"
TEMPLATES_DIR = FLOWS_DIR / ".templates"


def get_active_flows():
    """List all active SDD flows with their status."""
    flows = []
    if not FLOWS_DIR.exists():
        return flows
    
    for item in FLOWS_DIR.iterdir():
        if item.is_dir() and item.name.startswith("sdd-"):
            status_file = item / "_status.md"
            if status_file.exists():
                content = status_file.read_text()
                # Extract current phase
                phase = "UNKNOWN"
                for line in content.split("\n"):
                    if line.startswith("**Current Phase:**"):
                        phase = line.replace("**Current Phase:**", "").strip()
                        break
                flows.append({"name": item.name, "phase": phase, "path": item})
    return flows


def start_flow(name: str):
    """Start a new SDD flow."""
    flow_dir = FLOWS_DIR / f"sdd-{name}"
    
    if flow_dir.exists():
        print(f"❌ Flow 'sdd-{name}' already exists.")
        print(f"   Use 'resume {name}' to continue or 'fork {name} <new-name>' to create a variant.")
        return
    
    # Create directory
    flow_dir.mkdir(parents=True, exist_ok=True)
    print(f"✓ Created directory: {flow_dir}")
    
    # Copy templates
    if TEMPLATES_DIR.exists():
        for template in TEMPLATES_DIR.iterdir():
            if template.is_file():
                dest = flow_dir / template.name
                content = template.read_text()
                # Replace placeholders
                content = content.replace("[FEATURE_NAME]", name.upper().replace("-", "_"))
                dest.write_text(content)
                print(f"  ✓ Copied template: {template.name}")
    else:
        print(f"⚠ Templates directory not found at {TEMPLATES_DIR}")
    
    # Initialize status
    status_file = flow_dir / "_status.md"
    if status_file.exists():
        content = status_file.read_text()
        content = content.replace("REQUIREMENTS | SPECIFICATIONS | PLAN | IMPLEMENTATION", "REQUIREMENTS")
        content = content.replace("DRAFTING | REVIEW | APPROVED | BLOCKED", "DRAFTING")
        content = content.replace("[DATE]", datetime.now().strftime("%Y-%m-%d"))
        content = content.replace("[AGENT/PERSON]", "Qwen")
        status_file.write_text(content)
    
    print(f"\n✓ SDD flow 'sdd-{name}' started in REQUIREMENTS phase")
    print("\nNext: Begin requirements elicitation")
    print("  - What problem are we solving?")
    print("  - Who are the users?")
    print("  - What are the acceptance criteria?")


def resume_flow(name: str):
    """Resume an existing SDD flow."""
    flow_dir = FLOWS_DIR / f"sdd-{name}"
    
    if not flow_dir.exists():
        print(f"❌ Flow 'sdd-{name}' not found.")
        print("   Use 'start {name}' to create a new flow.")
        return
    
    status_file = flow_dir / "_status.md"
    if not status_file.exists():
        print(f"⚠ No _status.md found in 'sdd-{name}'")
        return
    
    content = status_file.read_text()
    
    # Extract key info
    phase = "UNKNOWN"
    blockers = []
    progress = []
    context = []
    
    in_blockers = False
    in_progress = False
    in_context = False
    
    for line in content.split("\n"):
        if line.startswith("**Current Phase:**"):
            phase = line.replace("**Current Phase:**", "").strip()
        elif line.startswith("## Blockers"):
            in_blockers = True
            in_progress = False
            in_context = False
        elif line.startswith("## Progress"):
            in_blockers = False
            in_progress = True
            in_context = False
        elif line.startswith("## Context Notes"):
            in_blockers = False
            in_progress = False
            in_context = True
        elif line.startswith("## "):
            in_blockers = False
            in_progress = False
            in_context = False
        elif in_blockers and line.strip().startswith("- "):
            blockers.append(line.strip()[2:])
        elif in_progress and line.strip().startswith("- ["):
            progress.append(line.strip())
        elif in_context and line.strip().startswith("- ["):
            context.append(line.strip())
    
    print(f"\n📁 Resuming: sdd-{name}")
    print(f"📊 Current Phase: {phase}")
    print()
    
    if blockers:
        print("⚠️  Blockers:")
        for b in blockers:
            print(f"   - {b}")
        print()
    
    print("📋 Progress:")
    for p in progress:
        print(f"   {p}")
    print()
    
    if context:
        print("📝 Context:")
        for c in context[:5]:  # Show first 5 items
            print(f"   {c}")
        if len(context) > 5:
            print(f"   ... and {len(context) - 5} more")
        print()
    
    # Read current phase document if exists
    phase_files = {
        "REQUIREMENTS": "01-requirements.md",
        "SPECIFICATIONS": "02-specifications.md",
        "PLAN": "03-plan.md",
        "IMPLEMENTATION": "04-implementation-log.md"
    }
    
    phase_doc = phase_files.get(phase.split()[0] if phase else None)
    if phase_doc:
        doc_path = flow_dir / phase_doc
        if doc_path.exists():
            print(f"📄 Current document: {phase_doc}")
            doc_content = doc_path.read_text()
            # Show first few lines
            lines = doc_content.split("\n")[:10]
            print("   Preview:")
            for line in lines:
                if line.strip():
                    print(f"   {line}")
            print()
    
    print("Ready to continue from current phase.")


def fork_flow(existing: str, new: str):
    """Fork an existing SDD flow."""
    existing_dir = FLOWS_DIR / f"sdd-{existing}"
    new_dir = FLOWS_DIR / f"sdd-{new}"
    
    if not existing_dir.exists():
        print(f"❌ Source flow 'sdd-{existing}' not found.")
        return
    
    if new_dir.exists():
        print(f"❌ Target flow 'sdd-{new}' already exists.")
        return
    
    # Copy entire directory
    shutil.copytree(existing_dir, new_dir)
    print(f"✓ Copied 'sdd-{existing}' to 'sdd-{new}'")
    
    # Update status file
    status_file = new_dir / "_status.md"
    if status_file.exists():
        content = status_file.read_text()
        
        # Update title
        content = content.replace(f"Status: sdd-{existing}", f"Status: sdd-{new}")
        
        # Add fork history
        fork_note = f"""
## Fork History

- Forked from: `sdd-{existing}` on {datetime.now().strftime("%Y-%m-%d")}
- Reason: Context recovery / scope adjustment
- Changes: Pending user input

"""
        # Insert after Context Notes section
        if "## Context Notes" in content:
            content = content.replace("## Context Notes", "## Fork History\n\n- Forked from: `sdd-{existing}` on {datetime.now().strftime('%Y-%m-%d')}\n- Reason: Context recovery / scope adjustment\n- Changes: Pending user input\n\n## Context Notes")
        
        status_file.write_text(content)
    
    print(f"\n✓ Flow 'sdd-{new}' ready for adjustments")
    print("What changes would you like to make to the requirements/specifications?")


def show_status():
    """Show all active SDD flows."""
    flows = get_active_flows()
    
    if not flows:
        print("No active SDD flows found.")
        print("\nUse 'start [name]' to create a new flow.")
        return
    
    print(f"\n📊 Active SDD Flows ({len(flows)})\n")
    print("-" * 60)
    
    for flow in flows:
        print(f"\n📁 {flow['name']}")
        print(f"   Phase: {flow['phase']}")
        print(f"   Path: {flow['path']}")
        
        # Read status for more details
        status_file = flow['path'] / "_status.md"
        if status_file.exists():
            content = status_file.read_text()
            # Extract last updated
            for line in content.split("\n"):
                if line.startswith("**Last Updated:**"):
                    print(f"   Updated: {line.replace('**Last Updated:**', '').strip()}")
                    break
    
    print("\n" + "-" * 60)
    print("\nUse 'resume [name]' to continue a flow")
    print("Use 'fork [name] [new-name]' to create a variant")


def show_help():
    """Show help information."""
    flows = get_active_flows()
    
    print(__doc__)
    
    if flows:
        print("\n📊 Current Active Flows:")
        for flow in flows:
            print(f"   - {flow['name']} ({flow['phase']})")


def main():
    args = sys.argv[1:]
    
    if not args or args[0] in ("help", "-h", "--help"):
        show_help()
        return
    
    command = args[0]
    
    if command == "start":
        if len(args) < 2:
            print("❌ Usage: start [name]")
            print("   Example: start my-feature")
            return
        start_flow(args[1])
    
    elif command == "resume":
        if len(args) < 2:
            print("❌ Usage: resume [name]")
            print("   Example: resume my-feature")
            return
        resume_flow(args[1])
    
    elif command == "fork":
        if len(args) < 3:
            print("❌ Usage: fork [existing-name] [new-name]")
            print("   Example: fork my-feature my-feature-v2")
            return
        fork_flow(args[1], args[2])
    
    elif command == "status":
        show_status()
    
    else:
        print(f"❌ Unknown command: {command}")
        show_help()


if __name__ == "__main__":
    main()
