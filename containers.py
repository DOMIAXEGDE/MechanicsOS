import random
import hashlib
from reportlab.lib.pagesizes import A4, A5, A3
from reportlab.pdfgen import canvas

# ============================================================
# USER CONFIG
# ============================================================

PAGE_SIZE_MAP = {
    "A4": A4,
    "A5": A5,
    "A3": A3,
}

NUM_PAGES       = 300
GRID_ROWS       = 6
GRID_COLS       = 4
SPLIT_MAX_DEPTH = 4
OUTPUT_FILE     = "containers.pdf"

SHAPES = [
    "vertical_rect",
    "horizontal_rect",
    "square",
    "split_square",
]

# ============================================================
# LAYOUT GENERATION
# ============================================================

def layout_signature(layout, seed=None):
    flat = []
    for row in layout:
        for cell in row:
            flat.append(f"{cell['type']}:{cell['depth']}")
    base = "|".join(flat)
    if seed is not None:
        base = f"{seed}:{base}"
    return hashlib.sha256(base.encode()).hexdigest()


def generate_random_layout(rows, cols, max_depth):
    layout = []
    for r in range(rows):
        row = []
        for c in range(cols):
            t = random.choice(SHAPES)
            d = random.randint(1, max_depth) if t == "split_square" else 0
            row.append({"type": t, "depth": d})
        layout.append(row)
    return layout

def generate_unique_layouts(n, rows, cols, max_depth):
    layouts = []
    seen = set()
    attempts = 0

    while len(layouts) < n:
        attempts += 1
        L = generate_random_layout(rows, cols, max_depth)
        sig = layout_signature(L, seed=None)

        if sig not in seen:
            seen.add(sig)
            layouts.append(L)

        if attempts > n * 50:
            print("Uniqueness limit reached.")
            break

    return layouts

# ============================================================
# DRAWING — PERFECT ALIGNMENT GUARANTEED
# ============================================================

def draw_split_square(c, x, y, w, h, depth):
    c.rect(x, y, w, h)

    if depth <= 0:
        return

    if random.random() < 0.5:
        # vertical split
        half = w / 2
        draw_split_square(c, x, y, half, h, depth - 1)
        draw_split_square(c, x + half, y, half, h, depth - 1)
    else:
        # horizontal split
        half = h / 2
        draw_split_square(c, x, y, w, half, depth - 1)
        draw_split_square(c, x, y + half, w, half, depth - 1)

def draw_cell_shape(c, x, y, w, h, cell):
    t = cell["type"]
    d = cell["depth"]

    if t == "vertical_rect":
        if random.random() < 0.5:
            c.rect(x, y, w/2, h)
        else:
            c.rect(x + w/2, y, w/2, h)

    elif t == "horizontal_rect":
        if random.random() < 0.5:
            c.rect(x, y, w, h/2)
        else:
            c.rect(x, y + h/2, w, h/2)

    elif t == "square":
        # Only allowed if cell is square; otherwise fallback to split
        if abs(w - h) < 1e-6:
            c.rect(x, y, w, h)
        else:
            draw_split_square(c, x, y, w, h, 1)

    elif t == "split_square":
        draw_split_square(c, x, y, w, h, d)

# ============================================================
# PDF GENERATION
# ============================================================

def create_pdf(page_size, page_label, layouts, rows, cols, filename):
    c = canvas.Canvas(filename, pagesize=page_size)
    W, H = page_size

    margin_x = W * 0.05
    margin_y = H * 0.05

    usable_w = W - 2 * margin_x
    usable_h = H - 2 * margin_y

    cell_w = usable_w / cols
    cell_h = usable_h / rows

    for i, layout in enumerate(layouts, start=1):
        c.setLineWidth(1)
        c.drawString(margin_x, H - margin_y + 5, f"( {i} )")

        for r in range(rows):
            for col in range(cols):
                x = margin_x + col * cell_w
                y = margin_y + r * cell_h
                draw_cell_shape(c, x, y, cell_w, cell_h, layout[r][col])

        c.showPage()

    c.save()
    print(f"Saved: {filename}")

# ============================================================
# MAIN
# ============================================================

def main():
    choice = input("Choose page size (A4 / A5 / A3): ").strip().upper()
    if choice not in PAGE_SIZE_MAP:
        print("Invalid choice.")
        return

    seed_input = input("Enter seed (leave blank for random): ").strip()

    if seed_input == "":
        seed = random.randrange(1_000_000_000)
        print(f"Generated random seed: {seed}")
    else:
        seed = int(seed_input)
        print(f"Using seed: {seed}")

    # Apply deterministic seed
    random.seed(seed)

    page_size = PAGE_SIZE_MAP[choice]

    print(f"Generating {NUM_PAGES} unique pages…")
    layouts = generate_unique_layouts(NUM_PAGES, GRID_ROWS, GRID_COLS, SPLIT_MAX_DEPTH)

    create_pdf(page_size, choice, layouts, GRID_ROWS, GRID_COLS, OUTPUT_FILE)

    print(f"Done. Seed used: {seed}")


if __name__ == "__main__":
    main()
