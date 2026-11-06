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
# # aiida-core
#
# This notebook builds the Quantum Espresso energy-volume-curve workflow directly with [`aiida-core`](https://github.com/aiidateam/aiida-core) and exports it as a PWD `workflow.json`. The second half of the notebook loads that same JSON file with `jobflow`, `pyiron_base` and `pyiron_workflow` to show that a graph built with one engine can be executed by another.

# %% [markdown]
# ## Define workflow with aiida
#
# `aiida-core` represents a workflow as a `GraphHandle` built from `task`s, each wrapping a Python function; connecting a task's output to another task's input builds up the graph. `load_profile()` connects to the local AiiDA profile/database, which is required before any AiiDA node can be created, since every task and its result are stored there for provenance.

# %%
from python_workflow_definition.aiida import write_workflow_json
from python_workflow_definition.shared import get_dict as _shared_get_dict

from aiida.engine import graph, task

workflow_json_filename = "aiida_qe.json"

# %%
from workflow import (
    generate_structures as _generate_structures,
    get_bulk_structure as _get_bulk_structure,
    calculate_qe as _calculate_qe,
    plot_energy_volume_curve as _plot_energy_volume_curve,
    collect_volumes as _collect_volumes,
    collect_energies as _collect_energies,
)

# %%
import typing as t
from typing import Any

from workflow import (
    generate_structures as _generate_structures,
    get_bulk_structure as _get_bulk_structure,
    calculate_qe as _calculate_qe,
    plot_energy_volume_curve as _plot_energy_volume_curve,
    collect_volumes as _collect_volumes,
    collect_energies as _collect_energies,
)


class QeOut(t.TypedDict):
    energy: Any
    volume: Any
    structure: Any


class StructOut(t.TypedDict):
    s_0: Any
    s_1: Any
    s_2: Any
    s_3: Any
    s_4: Any


def get_bulk_structure(element, a, cubic) -> Any:
    return _get_bulk_structure(element=element, a=a, cubic=cubic)


get_bulk_structure.__module__ = "workflow"
get_bulk_structure = task(get_bulk_structure)


def get_dict(structure, calculation, kpts, pseudopotentials, smearing) -> Any:
    return _shared_get_dict(structure=structure, calculation=calculation, kpts=kpts, pseudopotentials=pseudopotentials, smearing=smearing)


get_dict.__module__ = "python_workflow_definition.shared"
get_dict = task(get_dict)


def calculate_qe(input_dict, working_directory) -> QeOut:
    return _calculate_qe(input_dict=input_dict, working_directory=working_directory)


calculate_qe.__module__ = "workflow"
calculate_qe = task(calculate_qe)


def generate_structures(structure, strain_lst) -> StructOut:
    return _generate_structures(structure=structure, strain_lst=strain_lst)


generate_structures.__module__ = "workflow"
generate_structures = task(generate_structures)


def collect_volumes(v0, v1, v2, v3, v4) -> Any:
    return _collect_volumes(v0, v1, v2, v3, v4)


collect_volumes.__module__ = "workflow"
collect_volumes = task(collect_volumes)


def collect_energies(v0, v1, v2, v3, v4) -> Any:
    return _collect_energies(v0, v1, v2, v3, v4)


collect_energies.__module__ = "workflow"
collect_energies = task(collect_energies)


def plot_energy_volume_curve(volume_lst, energy_lst) -> Any:
    return _plot_energy_volume_curve(volume_lst=volume_lst, energy_lst=energy_lst)


plot_energy_volume_curve.__module__ = "workflow"
plot_energy_volume_curve = task(plot_energy_volume_curve)


# %%
@graph
def qe_eos(element="Al", a=4.04, cubic=True, relax_workdir="mini",
            pseudopotentials={"Al": "Al.pbe-n-kjpaw_psl.1.0.0.UPF"},
            kpts=[3, 3, 3], calc_type_relax="vc-relax",
            calc_type_scf="scf", smearing=0.02,
            strain_lst=[0.9, 0.95, 1.0, 1.05, 1.1]):
    bulk = get_bulk_structure(element=element, a=a, cubic=cubic)
    relax_inputs = get_dict(structure=bulk, calculation=calc_type_relax, kpts=kpts, pseudopotentials=pseudopotentials, smearing=smearing)
    relaxed = calculate_qe(input_dict=relax_inputs, working_directory=relax_workdir)
    strained = generate_structures(structure=relaxed["structure"], strain_lst=strain_lst)
    scf_inputs_0 = get_dict(structure=strained["s_0"], calculation=calc_type_scf, kpts=kpts, pseudopotentials=pseudopotentials, smearing=smearing)
    scf_0 = calculate_qe(input_dict=scf_inputs_0, working_directory="strain_0")
    scf_inputs_1 = get_dict(structure=strained["s_1"], calculation=calc_type_scf, kpts=kpts, pseudopotentials=pseudopotentials, smearing=smearing)
    scf_1 = calculate_qe(input_dict=scf_inputs_1, working_directory="strain_1")
    scf_inputs_2 = get_dict(structure=strained["s_2"], calculation=calc_type_scf, kpts=kpts, pseudopotentials=pseudopotentials, smearing=smearing)
    scf_2 = calculate_qe(input_dict=scf_inputs_2, working_directory="strain_2")
    scf_inputs_3 = get_dict(structure=strained["s_3"], calculation=calc_type_scf, kpts=kpts, pseudopotentials=pseudopotentials, smearing=smearing)
    scf_3 = calculate_qe(input_dict=scf_inputs_3, working_directory="strain_3")
    scf_inputs_4 = get_dict(structure=strained["s_4"], calculation=calc_type_scf, kpts=kpts, pseudopotentials=pseudopotentials, smearing=smearing)
    scf_4 = calculate_qe(input_dict=scf_inputs_4, working_directory="strain_4")
    volumes = collect_volumes(v0=scf_0["volume"], v1=scf_1["volume"], v2=scf_2["volume"], v3=scf_3["volume"], v4=scf_4["volume"])
    energies = collect_energies(v0=scf_0["energy"], v1=scf_1["energy"], v2=scf_2["energy"], v3=scf_3["energy"], v4=scf_4["energy"])
    return {"result": plot_energy_volume_curve(volume_lst=volumes, energy_lst=energies)}



# %%
write_workflow_json(qe_eos, file_name=workflow_json_filename)

# %%
# !cat {workflow_json_filename}

# %% [markdown]
# ## Load Workflow with jobflow
#
# `load_workflow_json` reconstructs the same graph as a `jobflow` `Flow` of `Job`s. To show that the loaded graph behaves like a native `jobflow` object, the lattice constant `a` of the first job is overridden (4.04 -> 4.05) before the flow is executed locally with `run_locally`.

# %%
from python_workflow_definition.jobflow import load_workflow_json

# %%
from jobflow.managers.local import run_locally

# %%
flow = load_workflow_json(file_name=workflow_json_filename)

# %%
flow[0].function_kwargs["a"] = 4.05

# %%
result = run_locally(flow)
result

# %% [markdown]
# ## Load Workflow with pyiron_base
#
# `pyiron_base`'s `load_workflow_json` turns each node into a delayed pyiron job. `.draw()` renders the dependency graph, and `.pull()` triggers execution of the whole chain, saving every intermediate job (relax + 5 strained SCF calculations) to the pyiron project.

# %%
from python_workflow_definition.pyiron_base import load_workflow_json

# %%
delayed_object_lst = load_workflow_json(file_name=workflow_json_filename)
delayed_object_lst[-1].draw()

# %%
delayed_object_lst[0].input['a'] = 4.05

# %%
delayed_object_lst[-1].pull()

# %% [markdown]
# ## Load Workflow with pyiron_workflow
#
# Finally, the same JSON is loaded into a `pyiron_workflow` `Workflow` object. Nodes become graph nodes reachable via attribute access (e.g. `wf.get_bulk_structure`), and `.run()` executes them in dependency order.

# %%
from python_workflow_definition.pyiron_workflow import load_workflow_json

# %%
wf = load_workflow_json(file_name=workflow_json_filename)

# %%
wf.get_bulk_structure.inputs.a.value = 4.05

# %%
wf.draw(size=(10,10))

# %%
wf.run()
