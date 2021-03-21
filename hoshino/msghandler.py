from os import name
from hoshino import CanceledException, message_preprocessor, trigger
from hoshino.typing import CQEvent


anonymous_list = {'default': {
    'no_anonymous': False,
    'anonymous': {}
}}

@message_preprocessor
async def handle_message(bot, event: CQEvent, _):

    if event.detail_type != 'group':
        return

    if (gid := event.group_id) not in anonymous_list:
        anonymous_list[gid] = anonymous_list['default']

    if event.sub_type == 'anonymous':
        anonymous = event.anonymous
        anonymous_list[gid]['anonymous'][anonymous['name']] = anonymous
        if anonymous_list[gid]['no_anonymous']:
            return

    for t in trigger.chain:
        sf = t.find_handler(event)
        if sf:
            if sf.only_to_me and not event['to_me']:
                sf = None
                continue  # not to me, ignore.
            if not sf.sv._check_all(event):
                sf = None
                continue  # permission denied.
            trigger_name = t.__class__.__name__
            break

    if not sf:
        event['iscmd'] = None
        return  # triggered nothing.
    event['iscmd'] = trigger_name
    sf.sv.logger.info(f'Message {event.message_id} triggered {sf.__name__} by {trigger_name}.')

    if sf.only_to_me and not event['to_me']:
        return  # not to me, ignore.

    if not sf.sv._check_all(event):
        return  # permission denied.

    try:
        await sf.func(bot, event)
    except CanceledException:
        raise
    except Exception as e:
        sf.sv.logger.error(f'{type(e)} occured when {sf.__name__} handling message {event.message_id}.')
        sf.sv.logger.exception(e)
    raise CanceledException(f'Handled by {trigger_name} of Hoshino')
