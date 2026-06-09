# ස්ටේබල් පයිතන් වර්ෂන් එකක් ගනිමු
FROM python:3.10-slim

# වීඩියෝ ඩවුන්ලෝඩ්/කන්වර්ට් වැඩවලට අනිවාර්යයෙන්ම ffmpeg ඕන නිසා ඒක දාගනිමු
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# සර්වර් එක ඇතුලේ වැඩ කරන ඩිරෙක්ටරිය
WORKDIR /app

# requirements.txt එක කොපි කරලා පැකේජ් ඉන්ස්ටෝල් කරමු
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ඉතුරු ඔක්කොම කෝඩ් ටික සර්වර් එකට කොපි කරමු
COPY . .

# සර්වර් එක ස්ටාර්ට් කරන කමාන්ඩ් එක
CMD ["python", "main.py"]
