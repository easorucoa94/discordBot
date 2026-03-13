import asyncio

disconnect_tasks = {}

class inactivityHelper:
    INACTIVITY_TIMER_IN_SECONDS = 5

    @staticmethod
    async def triggerDisconnect(guild):
        await asyncio.sleep(inactivityHelper.INACTIVITY_TIMER_IN_SECONDS)

        vc = guild.voice_client
        if vc and not vc.is_playing() and not vc.is_paused():
            await vc.disconnect()
            await guild.text_channels[0].send(f"I'm leaving the channel due to inactivity ({inactivityHelper.INACTIVITY_TIMER_IN_SECONDS} seconds), bye!")

    @staticmethod
    def runInactivityTimer(guild):
        vc = guild.voice_client
        if not vc:
            return
            
        loop = vc.client.loop
        
        def do_schedule():
            # cancel existing timer
            if guild.id in disconnect_tasks:
                disconnect_tasks[guild.id].cancel()

            disconnect_tasks[guild.id] = loop.create_task(
                inactivityHelper.triggerDisconnect(guild)
            )
            
        loop.call_soon_threadsafe(do_schedule)
        
    @staticmethod
    def cancelTimer(guild):
        if guild.id in disconnect_tasks:
            disconnect_tasks[guild.id].cancel()
            del disconnect_tasks[guild.id]