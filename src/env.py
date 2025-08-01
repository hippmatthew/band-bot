import os
from typing import cast

_DISC_TOKEN: str | None = os.getenv('DISC_TOKEN')
_GUILD_ID: str | None = os.getenv('GUILD_ID')
_CHANNEL_ID: str | None = os.getenv('CHANNEL_ID')
_JBC_URL: str | None = os.getenv('JBC_URL')
_JBM_URL: str | None = os.getenv('JBM_URL')

def disc_token() -> str:
  return cast(str, _DISC_TOKEN)

def guild_id() -> int:
  return int(cast(str, _GUILD_ID))

def channel_id() -> int:
  return int(cast(str, _CHANNEL_ID))

def jbc_url() -> str:
  return cast(str, _JBC_URL)

def jbm_url() -> str:
  return cast(str, _JBM_URL)

def check_env() -> str:
  error_str: str = ''
  if not _DISC_TOKEN:
    error_str += '\n\tmissing discord token'

  if not _GUILD_ID:
    error_str += '\n\tmissing guild id'

  if not _CHANNEL_ID:
    error_str += '\n\tmissing channel id'

  if not _JBC_URL:
    error_str += '\n\tmissing jazz bar classics url'

  if not _JBM_URL:
    error_str += '\n\tmissing jazz bar masterpieces url'

  return error_str