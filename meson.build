project('presentat',
          version: '0.1.0',
    meson_version: '>= 1.0.0',
  default_options: [ 'warning_level=2', 'werror=false', ],
)

i18n = import('i18n')
gnome = import('gnome')

subdir('data')
subdir('src')
subdir('po')
dependencies = [ dependency('gtk4', version: '>= 4.12'),
    dependency('libadwaita-1', version: '>= 1.7'),
    dependency('webkitgtk-6.0', version: '>= 2.40.1') ]
gnome.post_install(
     glib_compile_schemas: true,
    gtk_update_icon_cache: true,
  update_desktop_database: true,
)
