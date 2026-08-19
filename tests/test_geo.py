from orbital_atlas.geo import earth_surface_scene_xyz, geodetic_to_scene_xyz


def test_greenwich_is_front():
    x, y, z = earth_surface_scene_xyz(0.0, 0.0)
    assert abs(x) < 1e-6
    assert abs(y) < 1e-6
    assert z < 0.0


def test_north_pole_is_positive_y():
    x, y, z = earth_surface_scene_xyz(90.0, 0.0)
    assert y > 0.0


def test_orbit_altitude_is_above_surface():
    surface = earth_surface_scene_xyz(0.0, 0.0)
    orbit = geodetic_to_scene_xyz(0.0, 0.0, 400.0)
    assert orbit is not None
    assert abs(orbit[2]) > abs(surface[2])
