project('presentat',
    version: '0.1.0',
    meson_version: '>= 1.0.0',
    default_options: [
        'warning_level=2',
        'werror=false',
    ],
)

# --- Define dependencies ---
# Find the python installation. This is crucial for building a Python app.
python = import('python').find_installation('python3')

# Define your application's GObject dependencies
dependencies = [
    dependency('gtk4', version: '>= 4.12'),
    dependency('libadwaita-1', version: '>= 1.7'),
    # Note: I'm keeping webkitgtk here as it's in your file, but you may not need it
    # if Marp CLI handles the rendering.
    dependency('webkitgtk-6.0', version: '>= 2.40.1')
]

# --- Subdirectories ---
# These lines tell Meson to look for additional build instructions in these folders.
subdir('data')
subdir('src')
subdir('po')

# --- Post-install actions ---
# This block is correctly defined to update the system's caches after installation.
gnome = import('gnome')
i18n = import('i18n')

gnome.post_install(
    glib_compile_schemas: true,
    gtk_update_icon_cache: true,
    update_desktop_database: true,
)