import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import pandas as pd
import ast

CSV_FILE = "length_7.csv"  # Your CSV file

# Load and sanitize data
df = pd.read_csv(CSV_FILE)
df.columns = df.columns.str.strip()
df['Pattern'] = df['Pattern'].apply(ast.literal_eval)
df['Complete'] = df['Complete'].astype(bool)

# Grid layout for 3x3 Android pattern
positions = {
    0: (0, 2), 1: (1, 2), 2: (2, 2),
    3: (0, 1), 4: (1, 1), 5: (2, 1),
    6: (0, 0), 7: (1, 0), 8: (2, 0)
}

sequences = df['Pattern'].tolist()
completed = df['Complete'].tolist()

# Start at first incomplete pattern
try:
    first_incomplete = completed.index(False)
except ValueError:
    first_incomplete = 0

current_index = [first_incomplete]

# Set up plot
fig, ax = plt.subplots(figsize=(6, 6))
plt.subplots_adjust(bottom=0.25)
ax.set_xlim(-1, 3)
ax.set_ylim(-1.5, 3)
ax.set_aspect('equal')
ax.axis('off')

title = ax.set_title("")

# Draw pattern function
def draw_pattern(index):
    ax.clear()
    ax.set_xlim(-1, 3)
    ax.set_ylim(-1.5, 3)
    ax.set_aspect('equal')
    ax.axis('off')

    seq = sequences[index]
    first_node = seq[0]

    # Draw nodes
    for i in range(9):
        x, y = positions[i]
        if i == first_node:
            ax.plot(x, y, 'ro', markersize=20)  # Red for first node
        else:
            ax.plot(x, y, 'ko', markersize=20)
        ax.text(x, y, str(i), color='white', ha='center', va='center', fontsize=12)

    # Draw pattern lines
    for i in range(len(seq) - 1):
        x1, y1 = positions[seq[i]]
        x2, y2 = positions[seq[i + 1]]
        color = 'green' if completed[index] else 'blue'
        ax.plot([x1, x2], [y1, y2], color=color, linewidth=3)

    # Update title and status
    total = len(completed)
    num_completed = completed.count(True)
    num_incomplete = completed.count(False)
    title.set_text(f"Pattern {index + 1} of {total}")

    if num_incomplete == 0:
        ax.text(1.5, -0.5, f"All patterns completed 🎉\n✓ Completed: {num_completed} ✗ Incomplete: {num_incomplete}",
                ha="center", fontsize=12)
    else:
        current_status = "✓ Completed" if completed[index] else "✗ Incomplete"
        ax.text(1.5, -0.5, f"{current_status}\n✓ Completed: {num_completed} ✗ Incomplete: {num_incomplete}",
                ha="center", fontsize=12)

    fig.canvas.draw()

# Save progress to CSV
def save_progress():
    df['Complete'] = completed
    df.to_csv(CSV_FILE, index=False)

# Navigation functions
def next_pattern(event):
    if current_index[0] < len(sequences) - 1:
        current_index[0] += 1
        draw_pattern(current_index[0])

def prev_pattern(event):
    if current_index[0] > 0:
        current_index[0] -= 1
        draw_pattern(current_index[0])

def mark_complete(event):
    completed[current_index[0]] = True
    save_progress()

    # Auto-advance to next incomplete pattern
    try:
        next_incomplete = completed.index(False, current_index[0] + 1)
        current_index[0] = next_incomplete
    except ValueError:
        # No remaining incomplete patterns
        pass

    draw_pattern(current_index[0])

# Add buttons
axprev = plt.axes([0.1, 0.05, 0.15, 0.075])
axnext = plt.axes([0.3, 0.05, 0.15, 0.075])
axmark = plt.axes([0.55, 0.05, 0.3, 0.075])

bnext = Button(axnext, 'Next')
bprev = Button(axprev, 'Previous')
bmark = Button(axmark, 'Mark as Complete')

bnext.on_clicked(next_pattern)
bprev.on_clicked(prev_pattern)
bmark.on_clicked(mark_complete)

# Initial draw
draw_pattern(current_index[0])
plt.show()
