# IX loopback runtime

UDP OSC on 127.0.0.1:9000 and health HTTP on 127.0.0.1:9100.

```bash
# from repo root
PYTHONPATH=runtime python3 -m ix_runtime
```

Or `npm run runtime`. Refuses `--host 0.0.0.0`.
