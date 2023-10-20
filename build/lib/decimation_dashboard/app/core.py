r"""
Define your classes and create the instances that you need to expose
"""
import logging
from trame.app import get_server
from trame.ui.vuetify import SinglePageLayout
from trame.widgets import vuetify, vtk

import pyvista as pv
from pyvista.trame import plotter_ui

pv.OFF_SCREEN = True
mesh = pv.Sphere()


# Read command line
import sys

if len(sys.argv) > 1:
    path = sys.argv[1]
    print(f"Reading {path}")
    try:
        mesh = pv.read(path)
    except:
        try:
            from pyvista import examples

            exec(f"mesh = examples.download_{path}()")
        except:
            mesh = pv.Sphere()

print(f"examples.download_{path}()")

pl = pv.Plotter()
pl.add_mesh(mesh, color="tan", show_edges=True)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# ---------------------------------------------------------
# Engine class
# ---------------------------------------------------------

# import fast_simplification
# points, faces = mesh.points, mesh.faces.reshape(-1, 4)[:, 1:]
# points_out, faces_out, collapses = fast_simplification.simplify(points, faces, 0.9, return_collapses=True)

from functools import cache


@cache
def decimate_mesh(resolution):
    return mesh.decimate(1 - resolution)


class Engine:
    def __init__(self, server=None):
        if server is None:
            server = get_server()

        self._server = server

        # initialize state + controller
        state, ctrl = server.state, server.controller

        # Set state variable
        state.trame__title = "decimation-dashboard"
        state.resolution = 6

        # Bind instance methods to controller
        ctrl.reset_resolution = self.reset_resolution
        ctrl.on_server_reload = self.ui

        # Bind instance methods to state change
        state.change("resolution")(self.on_resolution_change)

        # Generate UI
        self.ui()

    @property
    def server(self):
        return self._server

    @property
    def state(self):
        return self.server.state

    @property
    def ctrl(self):
        return self.server.controller

    def show_in_jupyter(self, **kwargs):
        from trame.app import jupyter

        logger.setLevel(logging.WARNING)
        jupyter.show(self.server, **kwargs)

    def reset_resolution(self):
        self._server.state.resolution = 0.5

    def on_resolution_change(self, resolution, **kwargs):
        pl.clear_actors()
        pl.add_mesh(decimate_mesh(resolution), color="tan", show_edges=True)
        # logger.info(f">>> ENGINE(a): Slider updating resolution to {resolution}")

    def ui(self, *args, **kwargs):
        with SinglePageLayout(self._server) as layout:
            # Toolbar
            layout.title.set_text(f"n points = {mesh.n_points}")
            with layout.toolbar:
                vuetify.VSpacer()
                vuetify.VSlider(  # Add slider
                    v_model=(
                        "resolution",
                        0.5,
                    ),  # bind variable with an initial value of 6
                    min=0.1,
                    max=1,
                    step=0.1,  # slider range
                    dense=True,
                    hide_details=True,  # presentation setup
                )
                with vuetify.VBtn(icon=True, click=self.ctrl.reset_camera):
                    vuetify.VIcon("mdi-crop-free")
                with vuetify.VBtn(icon=True, click=self.ctrl.reset_resolution):
                    vuetify.VIcon("mdi-undo")

            # Main content
            with layout.content:
                plotter_ui(pl)
                # with vuetify.VContainer(fluid=True, classes="pa-0 fill-height"):
                #     with vtk.VtkView() as vtk_view:                # vtk.js view for local rendering
                #         self.ctrl.reset_camera = vtk_view.reset_camera  # Bind method to controller
                #         with vtk.VtkGeometryRepresentation():      # Add representation to vtk.js view
                #             vtk.VtkAlgorithm(                      # Add ConeSource to representation
                #                 vtk_class="vtkConeSource",          # Set attribute value with no JS eval
                #                 state=("{ resolution }",)          # Set attribute value with JS eval
                #             )

            # Footer
            # layout.footer.hide()


def create_engine(server=None):
    # Get or create server
    if server is None:
        server = get_server()

    if isinstance(server, str):
        server = get_server(server)

    return Engine(server)
