import asyncio

disconnect_tasks = {}

class inactivityHelper:
    INACTIVITY_TIMER_IN_SECONDS = 5

    @staticmethod
    async def triggerDisconnect(guild):
        await asyncio.sleep(inactivityHelper.INACTIVITY_TIMER_IN_SECONDS)

        voiceClient = guild.voice_client
        if voiceClient and not voiceClient.is_playing() and not voiceClient.is_paused():
            await voiceClient.disconnect()
            await guild.text_channels[0].send(f"I'm leaving the channel due to inactivity ({inactivityHelper.INACTIVITY_TIMER_IN_SECONDS} seconds), bye!")

    @staticmethod
    def runInactivityTimer(guild):
        voiceClient = guild.voice_client
        if not voiceClient:
            return
            
        stalkCog = voiceClient.client.get_cog("Stalk Commands")
        if stalkCog and stalkCog.stalkTarget is not None:
            stalkTargetMember = guild.get_member(stalkCog.stalkTarget)
            if stalkTargetMember and stalkTargetMember.voice:
                inactivityHelper.cancelTimer(guild)
                return
            
        loop = voiceClient.client.loop
        
        def do_schedule():
            inactivityHelper.cancelTimer(guild)

            disconnect_tasks[guild.id] = loop.create_task(
                inactivityHelper.triggerDisconnect(guild)
            )
            
        loop.call_soon_threadsafe(do_schedule)
        
    @staticmethod
    def cancelTimer(guild):
        if guild.id in disconnect_tasks:
            disconnect_tasks[guild.id].cancel()
            del disconnect_tasks[guild.id]