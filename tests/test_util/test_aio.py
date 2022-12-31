import asyncio
import pytest

from dolor import *

@pytest.mark.asyncio
async def test_value_holder():
    async def set_task(holder):
        holder.set(1)

    holder = util.AsyncValueHolder()

    task = asyncio.create_task(set_task(holder))

    assert await holder.get() == 1

    await task
