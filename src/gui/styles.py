"""
src/gui/styles.py
Clean stylesheet that plays nice with BOTH Light and Dark themes.
"""
STYLESHEET = """
/* ----- General Widgets ----- */
QWidget {
    font-family: "Segoe UI", sans-serif;
    font-size: 13px;
}

/* ----- Splitters ----- */
QSplitter::handle {
    background-color: palette(mid); 
    width: 2px;
}
QSplitter::handle:hover { 
    background-color: #0d6efd; 
}

/* ----- Gallery Cards & Inputs ----- */
QLineEdit#ToolbarPath {
    background-color: palette(base);
    color: palette(text);
    border: 1px solid palette(mid);
    border-radius: 4px;
    padding: 6px;
}

QLabel#SubHeader {
    color: #0d6efd;
    font-size: 11px;
    font-weight: bold;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 6px;
}

/* ----- Progress Bar ----- */
QProgressBar {
    border: 1px solid palette(mid);
    border-radius: 6px;
    text-align: center;
    background-color: palette(base);
}
QProgressBar::chunk {
    background-color: #198754;
    border-radius: 6px;
}

# Add or update these specific entries in src/gui/styles.py


/* ... existing styles ... */

/* Ensures the toolbar inputs are readable in dark mode */
QLineEdit#ToolbarPath {
    background-color: palette(base);
    color: palette(text);
    border: 1px solid palette(mid);
    border-radius: 4px;
    padding: 6px;
}

/* Fixes the Progress Bar text contrast */
QProgressBar {
    border: 1px solid palette(mid);
    border-radius: 4px;
    text-align: center;
    background-color: palette(base);
    color: palette(text); /* Makes percentage visible */
    font-weight: bold;
}

QProgressBar::chunk {
    background-color: #0d6efd;
    border-radius: 2px;
}

"""