# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.6
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # Aiida
#
# https://github.com/BAMresearch/NFDI4IngScientificWorkflowRequirements
#
# This notebook defines the NFDI4Ing file-based workflow benchmark with [`aiida-core`](https://github.com/aiidateam/aiida-core) and then loads the resulting `workflow.json` into `jobflow`, `pyiron_base` and `pyiron_workflow` to show that the same JSON file can be executed by different engines. Every stage of the workflow calls an external command-line tool (`gmsh`, `meshio`, a FEniCS-based Poisson solver, ParaView's `pvbatch`, `tectonic`) in its own conda environment and passes file paths between stages rather than in-memory Python objects — see [`workflow.py`](workflow.py) for the six pipeline functions.

# %% [markdown]
# ## Define workflow with aiida
#
# `aiida-core` represents a workflow as a `GraphHandle` of `@task`s. `load_profile()` connects to the local AiiDA profile/database that stores provenance and results for every task. `generate_mesh`, `plot_over_line`, `substitute_macros` and `compile_paper` each return a single value and can be added to the graph unchanged, but `convert_to_xdmf` and `poisson` return a `dict`, so they are wrapped in `@task` functions returning a `TypedDict`, exposing each dictionary key as its own output that later tasks can connect to.

# %%
import os

# %%
from python_workflow_definition.aiida import write_workflow_json

from aiida.engine import graph, task


# %%
import typing as t
from typing import Any

from workflow import (
    generate_mesh as _generate_mesh,
    convert_to_xdmf as _convert_to_xdmf,
    poisson as _poisson,
    plot_over_line as _plot_over_line,
    substitute_macros as _substitute_macros,
    compile_paper as _compile_paper,
)


class XdmfOut(t.TypedDict):
    xdmf_file: Any
    h5_file: Any


class PoissonOut(t.TypedDict):
    numdofs: Any
    pvd_file: Any
    vtu_file: Any


def generate_mesh(domain_size, source_directory) -> Any:
    return _generate_mesh(domain_size=domain_size, source_directory=source_directory)


generate_mesh.__module__ = "workflow"
generate_mesh = task(generate_mesh)


def convert_to_xdmf(gmsh_output_file) -> XdmfOut:
    return _convert_to_xdmf(gmsh_output_file)


convert_to_xdmf.__module__ = "workflow"
convert_to_xdmf = task(convert_to_xdmf)


def poisson(meshio_output_xdmf, meshio_output_h5, source_directory) -> PoissonOut:
    return _poisson(meshio_output_xdmf, meshio_output_h5, source_directory)


poisson.__module__ = "workflow"
poisson = task(poisson)


def plot_over_line(poisson_output_pvd_file, poisson_output_vtu_file, source_directory) -> Any:
    return _plot_over_line(poisson_output_pvd_file, poisson_output_vtu_file, source_directory)


plot_over_line.__module__ = "workflow"
plot_over_line = task(plot_over_line)


def substitute_macros(pvbatch_output_file, ndofs, domain_size, source_directory) -> Any:
    return _substitute_macros(pvbatch_output_file, ndofs, domain_size, source_directory)


substitute_macros.__module__ = "workflow"
substitute_macros = task(substitute_macros)


def compile_paper(macros_tex, plot_file, source_directory) -> Any:
    return _compile_paper(macros_tex, plot_file, source_directory)


compile_paper.__module__ = "workflow"
compile_paper = task(compile_paper)

# %%
source_directory = os.path.abspath(os.path.join(os.curdir, "source"))

# %%
domain_size = 2.0


# %%
@graph
def nfdi(source_directory, domain_size=2.0):
    gmsh_output = generate_mesh(domain_size=domain_size, source_directory=source_directory)
    meshio_output = convert_to_xdmf(gmsh_output_file=gmsh_output)
    poisson_output = poisson(meshio_output_xdmf=meshio_output["xdmf_file"], meshio_output_h5=meshio_output["h5_file"], source_directory=source_directory)
    pvbatch_output = plot_over_line(poisson_output_pvd_file=poisson_output["pvd_file"], poisson_output_vtu_file=poisson_output["vtu_file"], source_directory=source_directory)
    macros_tex = substitute_macros(pvbatch_output_file=pvbatch_output, ndofs=poisson_output["numdofs"], domain_size=domain_size, source_directory=source_directory)
    return {"paper": compile_paper(macros_tex=macros_tex, plot_file=pvbatch_output, source_directory=source_directory)}


# %%
workflow_json_filename = "aiida_nfdi.json"

# %%
write_workflow_json(
    nfdi,
    file_name=workflow_json_filename,
    inputs={"source_directory": source_directory},
)

# %%
# !cat {workflow_json_filename}

# %% [markdown]
# ## Load Workflow with jobflow
#
# `python_workflow_definition.jobflow.load_workflow_json` reconstructs the same six-stage pipeline as a jobflow `Flow`, purely from `aiida_nfdi.json` — no reference to the `aiida-core` objects defined above. `run_locally` then executes the jobs in dependency order, re-running `gmsh`, `meshio`, the Poisson solver, `pvbatch` and `tectonic` exactly as before.

# %%
from python_workflow_definition.jobflow import load_workflow_json

# %%
from jobflow.managers.local import run_locally

# %%
flow = load_workflow_json(file_name=workflow_json_filename)

# %%
result = run_locally(flow)
result

# %% [markdown]
# ## Load Workflow with pyiron_base
#
# `python_workflow_definition.pyiron_base.load_workflow_json` turns the JSON graph into a list of delayed pyiron jobs; `.draw()` visualizes their dependencies and `.pull()` triggers execution, running each job in turn and returning the final `paper.pdf` path.

# %%
from python_workflow_definition.pyiron_base import load_workflow_json

# %%
delayed_object_lst = load_workflow_json(file_name=workflow_json_filename)
delayed_object_lst[-1].draw()

# %%
delayed_object_lst[-1].pull()

# %% [markdown]
# ## Load Workflow with pyiron_workflow
#
# Finally, the same JSON is loaded into a `pyiron_workflow` `Workflow` object. `.draw()` shows the node graph and `.run()` executes it end to end, again shelling out to each external tool in turn.

# %%
from python_workflow_definition.pyiron_workflow import load_workflow_json

# %%
wf = load_workflow_json(file_name=workflow_json_filename)

# %%
wf.draw(size=(10,10))

# %%
wf.run()
