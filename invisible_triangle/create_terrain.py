import sys
import math

import numpy as np
import direct.gui.DirectGuiGlobals as DGG
from panda3d.bullet import BulletWorld, BulletDebugNode, BulletRigidBodyNode
from panda3d.bullet import BulletHeightfieldShape, ZUp
from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import globalClock
from direct.gui.DirectGui import DirectFrame, DirectLabel, DirectSlider
from panda3d.core import load_prc_file_data
from panda3d.core import Filename, PNMImage
from panda3d.core import Shader, TextureStage, TransparencyAttrib
from panda3d.core import NodePath, TextNode
from panda3d.core import Point3, Vec3, Vec2, BitMask32, Vec4
from panda3d.core import OrthographicLens, Camera, MouseWatcher, PGTop
from panda3d.core import GeoMipTerrain


load_prc_file_data("", """
    textures-power-2 none
    gl-coordinate-system default
    window-title Panda3D Test Terrain
    filled-wireframe-apply-shader true
    stm-max-views 8
    stm-max-chunk-count 2048""")


class TestTerrain(ShowBase):

    def __init__(self):
        super().__init__()
        self.disable_mouse()

        self.world = BulletWorld()
        self.world.set_gravity(Vec3(0, 0, -9.81))
        self.debug = self.render.attach_new_node(BulletDebugNode('debug'))
        self.world.set_debug_node(self.debug.node())

        self.dragging = False
        self.clicked = False
        self.before_mouse_pos = Vec2()

        self.display_root = NodePath('camera_root')
        self.display_root.reparent_to(self.render)

        self.generate_terrain()
        self.create_display_region()
        self.create_gui_region()
        self.gui = Gui()

        self.accept('escape', sys.exit)
        self.accept('d', self.toggle_debug)
        self.accept('mouse1', self.mouse_click)
        self.accept('mouse1-up', self.mouse_release)
        self.taskMgr.add(self.update, 'update')

    def calc_aspect_ratio(self, display_region):
        """Args:
            display_region (Vec4): (left, right, bottom, top)
            The range is from 0 to 1.
            0: the left and bottom; 1: the right and top.
        """
        props = self.win.get_properties()
        window_size = props.get_size()

        region_w = display_region.y - display_region.x
        region_h = display_region.w - display_region.z
        display_w = int(window_size.x * region_w)
        display_h = int(window_size.y * region_h)

        gcd = math.gcd(display_w, display_h)
        w = display_w / gcd
        h = display_h / gcd
        aspect_ratio = w / h

        return aspect_ratio

    def calc_scale(self, region_size):
        aspect_ratio = self.get_aspect_ratio()

        w = region_size.y - region_size.x
        h = region_size.w - region_size.z
        new_aspect_ratio = aspect_ratio * w / h

        if aspect_ratio > 1.0:
            s = 1. / h
            return Vec3(s / new_aspect_ratio, 1.0, s)
        else:
            s = 1.0 / w
            return Vec3(s, 1.0, s * new_aspect_ratio)

    def create_gui_region(self):
        """Create the custom 2D region for slider and label.
        """
        # (left, right, bottom, top)
        region_size = Vec4(0.0, 1.0, 0.0, 0.1)
        region = self.win.make_display_region(region_size)
        region.set_sort(20)
        region.set_clear_color((0.5, 0.5, 0.5, 1.0))
        region.set_clear_color_active(True)

        gui_cam = NodePath(Camera('cam2d'))
        lens = OrthographicLens()
        lens.set_film_size(2, 2)
        lens.set_near_far(-1000, 1000)
        gui_cam.node().set_lens(lens)

        gui_render2d = NodePath('gui_render2d')
        gui_render2d.set_depth_test(False)
        gui_render2d.set_depth_write(False)
        gui_cam.reparent_to(gui_render2d)
        region.set_camera(gui_cam)

        self.gui_aspect2d = gui_render2d.attach_new_node(PGTop('gui_aspect2d'))
        scale = self.calc_scale(region_size)
        self.gui_aspect2d.set_scale(scale)

        mw2d_node = self.create_mouse_watcher('mw2d', region)
        self.gui_aspect2d.node().set_mouse_watcher(mw2d_node)

    def create_display_region(self):
        """Create the region to display terrain.
        """
        # (left, right, bottom, top)
        region_size = Vec4(0.0, 1.0, 0.1, 1.0)
        region = self.win.make_display_region(region_size)

        self.display_cam = NodePath(Camera('cam3d'))
        aspect_ratio = self.calc_aspect_ratio(region_size)
        self.display_cam.node().get_lens().set_aspect_ratio(aspect_ratio)
        region.set_camera(self.display_cam)
        self.camNode.set_active(False)

        self.display_cam.set_pos(Point3(0, self.img_size.y * -1, 200))
        self.display_cam.look_at(Point3(0, 0, 0))
        self.display_cam.reparent_to(self.display_root)
        self.display_mw = self.create_mouse_watcher('mw3d', region)

    def create_mouse_watcher(self, name, display_region):
        mw_node = MouseWatcher(name)
        input_ctrl = self.mouseWatcher.get_parent()
        input_ctrl.attach_new_node(mw_node)
        mw_node.set_display_region(display_region)
        return mw_node

    def toggle_debug(self):
        # self.toggle_wireframe()
        if self.debug.is_hidden():
            self.debug.show()
        else:
            self.debug.hide()

    def mouse_click(self):
        self.dragging = True
        self.dragging_start_time = globalClock.get_frame_time()

    def mouse_release(self):
        if globalClock.get_frame_time() - self.dragging_start_time < 0.2:
            self.clicked = True

        self.dragging = False
        self.before_mouse_pos.x = 0
        self.before_mouse_pos.y = 0

    def generate_terrain(self):
        self.terrain_root = NodePath(BulletRigidBodyNode('terrain_root'))
        self.terrain_root.node().set_mass(0)
        self.terrain_root.set_collide_mask(BitMask32.bit(1))

        self.terrain_root.reparent_to(self.display_root)
        heightmap = 'terrain/sample_1.png'
        height = 50

        img = PNMImage(Filename(heightmap))
        shape = BulletHeightfieldShape(img, height, ZUp)
        shape.set_use_diamond_subdivision(True)
        self.terrain_root.node().add_shape(shape)

        self.world.attach(self.terrain_root.node())

        self.terrain = GeoMipTerrain('geomip_terrain')
        self.terrain.set_heightfield(heightmap)
        self.terrain.set_border_stitching(True)
        self.terrain.set_block_size(8)
        self.terrain.set_min_level(2)
        self.terrain.set_focal_point(self.camera)

        self.img_size = img.get_size()
        x = (self.img_size.x - 1) / 2
        y = (self.img_size.y - 1) / 2
        self.terrain_pos = Point3(-x, -y, -(height / 2))
        scale = Vec3(1, 1, height)
        self.gmp_root = self.terrain.get_root()
        self.gmp_root.set_scale(scale)
        self.gmp_root.set_pos(self.terrain_pos)

        self.terrain.generate()
        self.gmp_root.reparent_to(self.terrain_root)

        # for mx, my in [(6, 4), (8, 12), (14, 6)]:
        #     self.hide_triangles(mx, my)

        shader = Shader.load(Shader.SL_GLSL, 'shaders/terrain_v.glsl', 'shaders/terrain_no_discard_f.glsl')
        self.gmp_root.set_shader(shader)
        tex_files = [('grass.png', 20), ('grass_04.jpg', 10)]

        for i, (file_name, tex_scale) in enumerate(tex_files):
            ts = TextureStage(f'ts{i}')
            ts.set_sort(i)
            self.gmp_root.set_shader_input(f'tex_ScaleFactor{i}', tex_scale)
            tex = self.loader.load_texture(f'textures/{file_name}')
            self.gmp_root.set_texture(ts, tex)

        # *************************************************************************************
        # When writing terrain to bam, is it necessarry to do flatten_strong for terrain.root?
        # Without flatten_strong, shaders did not work well when making model from the bam.
        # And, attempting to write terrain to bam after setting shader caused an error.
        # I could not find the way of making the part of triangles in a block invisible. 
        # TODO: try again about above.
        # self.gmp_root.flatten_strong()
        # self.gmp_root.writeBamFile('test3.bam')
        # *************************************************************************************

    def rotate_camera(self, mouse_pos, dt):
        angle = 0

        if (delta := mouse_pos.x - self.before_mouse_pos.x) < 0:
            angle -= 90
        elif delta > 0:
            angle += 90

        angle *= dt
        self.terrain_root.set_h(self.terrain_root.get_h() + angle)
        self.before_mouse_pos.x = mouse_pos.x

    def hide_triangles(self, mx, my):
        """Args:
                mx and my must be integer.
        """
        block_np = self.terrain.get_block_node_path(mx, my)
        geom = block_np.node().modify_geom(0)
        vdata = geom.modify_vertex_data()
        v_array = vdata.modify_array(0)
        view = memoryview(v_array).cast('B').cast('f')
        view[:] = np.zeros(len(view), dtype=np.float32)
        self.terrain.update()

    def get_block_pos(self, mouse_pos):
        near_pos = Point3()
        far_pos = Point3()

        lens = self.display_cam.node().get_lens()
        lens.extrude(mouse_pos, near_pos, far_pos)
        from_pos = self.display_root.get_relative_point(self.display_cam, near_pos)
        to_pos = self.display_root.getRelativePoint(self.display_cam, far_pos)

        if (result := self.world.ray_test_closest(
                from_pos, to_pos, mask=BitMask32.bit(1))).has_hit():
            hit_pos = result.get_hit_pos()
            pos = self.terrain_root.get_relative_point(self.display_root, hit_pos)
            rel_pos = pos - self.terrain_pos
            block_pos = self.terrain.get_block_from_pos(*rel_pos.xy)
            x, y = int(block_pos.x), int(block_pos.y)
            return x, y

    def update(self, task):
        dt = globalClock.get_dt()

        if self.display_mw.has_mouse():
            mouse_pos = self.display_mw.get_mouse()

            if self.dragging:
                if globalClock.get_frame_time() - self.dragging_start_time >= 0.2:
                    self.rotate_camera(mouse_pos, dt)

            if self.clicked:
                if pos := self.get_block_pos(mouse_pos):
                    mx, my = pos
                    self.hide_triangles(mx, my)
                    self.gui.show_info(f"Hole: GeomNode gmm{mx}x{my}")
                    self.clicked = False

        self.world.do_physics(dt)
        return task.cont


class Gui(DirectFrame):

    def __init__(self):
        super().__init__(
            parent=base.gui_aspect2d,
            frameColor=(.5, .5, .5, 0),
            frameSize=(-1, 1, -1, 1),
            pos=Point3(0, 0, 0),
        )
        self.initialiseoptions(type(self))
        self.set_transparency(TransparencyAttrib.MAlpha)
        self.create_widgets()

    def create_widgets(self):
        DirectLabel(
            parent=self,
            pos=Point3(-1.1, 0, 0),
            frameColor=(1, 1, 1, 0),
            text_scale=0.06,
            text_fg=(1, 1, 1, 1),
            text='zoom',
            text_align=TextNode.ARight,
        )

        self.slider = DirectSlider(
            parent=self,
            pos=(-0.32, 0, 0.01),
            scale=0.5,
            frameSize=(-1.5, 1.2, -0.1, 0.1),
            range=(100, 0),
            thumb_frameSize=(-0.02, 0.02, -0.1, 0.1),
            thumb_frameColor=(1, 1, 1, 1),
            thumb_relief=DGG.FLAT,
            value=100,
            command=self.zoom
        )

        self.label = DirectLabel(
            parent=self,
            pos=Point3(0.4, 0, 0),
            frameColor=(1, 1, 1, 0),
            text_scale=0.06,
            text_fg=(1, 1, 1, 1),
            text='',
            text_align=TextNode.ALeft,
        )

    def zoom(self):
        if (val := self.slider['value']) > 0:
            z = 200 * val / 100
            base.display_cam.set_z(base.render, z)
            base.display_cam.look_at(base.terrain_root)

    def show_info(self, text):
        self.label.setText(text)
        print(text)


if __name__ == '__main__':
    app = TestTerrain()
    app.run()