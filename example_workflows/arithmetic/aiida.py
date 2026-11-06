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
# This notebook defines the arithmetic workflow with [`aiida-core`](https://github.com/aiidateam/aiida-core) and then loads the resulting `workflow.json` into `jobflow`, `pyiron_base` and `pyiron_workflow`, to demonstrate that the same workflow definition can be executed by several different engines.

# %% [markdown]
# ## Define workflow with aiida
#
# `aiida-core` represents a workflow as a `GraphHandle` of `@task`s. Tasks are executed and stored by the AiiDA engine, so we first need to connect to an AiiDA profile with `load_profile()` before any task can run.

# %%
from python_workflow_definition.aiida import write_workflow_json

from aiida.engine import graph, task

workflow_json_filename = "aiida_simple.json"

# %%
import typing as t
from typing import Any

from workflow import (
    get_sum as _get_sum,
    get_prod_and_div as _get_prod_and_div,
    get_square as _get_square,
)


class ProdDiv(t.TypedDict):
    prod: Any
    div: Any


def get_prod_and_div(x, y) -> ProdDiv:
    return _get_prod_and_div(x, y)


get_prod_and_div.__module__ = "workflow"
get_prod_and_div = task(get_prod_and_div)


def get_sum(x, y) -> Any:
    return _get_sum(x, y)


get_sum.__module__ = "workflow"
get_sum = task(get_sum)


def get_square(x) -> Any:
    return _get_square(x)


get_square.__module__ = "workflow"
get_square = task(get_square)


# %%
@graph
def arithmetic(x=1, y=2):
    prod_div = get_prod_and_div(x=x, y=y)
    total = get_sum(x=prod_div["prod"], y=prod_div["div"])
    return {"result": get_square(x=total)}


# %%
write_workflow_json(arithmetic, workflow_json_filename)

# %%
# !cat {workflow_json_filename}

# %% [markdown]
# ## Load Workflow with jobflow
#
# The same `workflow.json` can now be loaded by a different engine. `python_workflow_definition.jobflow.load_workflow_json` reconstructs a jobflow `Flow` from the JSON, which is then executed locally with `run_locally`.

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
# The same JSON file is loaded into `pyiron_base`, producing a list of delayed jobs. `.draw()` visualizes the dependency graph and `.pull()` triggers delayed execution, running each job in turn and returning the final result.

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
# Finally, the workflow is loaded into `pyiron_workflow`, producing a `Workflow` object whose node graph can be visualized with `.draw()` and executed with `run_get_node`.

# %%
from python_workflow_definition.pyiron_workflow import load_workflow_json

# %%
wf = load_workflow_json(file_name=workflow_json_filename)

# %%
wf.draw(size=(10,10))

# %%
wf.run()
