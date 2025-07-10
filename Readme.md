```
+-----------------------------------------------+
| User (or External App)                        |
|    Sends high-level report request            |
+-------------------------------+---------------+
                                |
                                v
+-------------------------------+---------------+
|         Manager #1 LLM Deployment             |
|    - Decomposes into subtasks                 |
|    - Reads prompt from ConfigMap              |
+-------------------------------+---------------+
                                |
                                v
+-------------------------------+---------------+
|         Manager #2 LLM Deployment             |
|    - For each subtask:                        |
|       * Plans technical approach              |
|       * Generates commands for Engineer       |
|       * Evaluates results                     |
|    - Reads prompt from ConfigMap              |
+-------------------------------+---------------+
                                |
                                v
+-------------------------------+---------------+
|         Engineer #1 LLM Deployment            |
|    - Converts instructions into commands      |
|    - Returns plausible outputs                |
|    - Reads prompt from ConfigMap              |
+-------------------------------+---------------+
```
