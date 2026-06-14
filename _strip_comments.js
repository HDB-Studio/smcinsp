const fs = require('fs');
const path = 'h:\\Users\\Administrator\\Desktop\\142\\databaseManager.js';
let code = fs.readFileSync(path, 'utf8');
let lines = code.split('\n');
let result = [];
let inBlockComment = false;

for (let line of lines) {
    if (inBlockComment) {
        if (line.includes('*/')) inBlockComment = false;
        result.push(line);
        continue;
    }
    const blockStart = line.includes('/*');
    const blockEnd = line.includes('*/');
    if (blockStart && !blockEnd) {
        inBlockComment = true;
        result.push(line);
        continue;
    }

    let inSingle = false, inDouble = false, inBacktick = false;
    let cutIndex = -1;
    for (let i = 0; i < line.length; i++) {
        const ch = line[i];
        const prev = i > 0 ? line[i - 1] : '';
        if (inSingle || inDouble || inBacktick) {
            if (ch === '\\' && (inDouble || inSingle)) { i++; continue; }
            if (ch === "'" && inSingle) inSingle = false;
            else if (ch === '"' && inDouble) inDouble = false;
            else if (ch === '`' && inBacktick) inBacktick = false;
        } else {
            if (ch === "'" && prev !== '\\') inSingle = true;
            else if (ch === '"' && prev !== '\\') inDouble = true;
            else if (ch === '`') inBacktick = true;
            else if (ch === '/' && line[i + 1] === '/') { cutIndex = i; break; }
        }
    }
    if (cutIndex >= 0) {
        const trimmed = line.substring(0, cutIndex).replace(/\s+$/, '');
        if (trimmed.length > 0) result.push(trimmed);
    } else {
        result.push(line);
    }
}
fs.writeFileSync(path, result.join('\n'), 'utf8');
console.log('完成，处理了 ' + lines.length + ' 行，结果 ' + result.length + ' 行');
