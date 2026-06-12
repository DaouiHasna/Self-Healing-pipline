const fs = require("fs/promises");
const path = require("path");

const dbPath = path.join(__dirname, "../data/tasks.json");

async function initDb() {
  try {
    await fs.access(dbPath);
  } catch {
    await fs.writeFile(dbPath, JSON.stringify([]));
  }
}

async function getAll() {
  await initDb();
  const data = await fs.readFile(dbPath, "utf-8");
  return JSON.parse(data);
}

async function getById(id) {
  const tasks = await getAll();
  return tasks.find(t => t.id === id);
}

async function add(title) {
  const tasks = await getAll();
  const task = { id: Date.now().toString(), title, done: false };
  tasks.push(task);
  await fs.writeFile(dbPath, JSON.stringify(tasks, null, 2));
  return task;
}

async function remove(id) {
  const tasks = await getAll();
  const newTasks = tasks.filter(t => t.id !== id);
  await fs.writeFile(dbPath, JSON.stringify(newTasks, null, 2));
  return newTasks;
}

async function getTaskCount() {
  const tasks = await getAll();
  return tasks.length;
}

module.exports = { getAll, getById, add, remove, getTaskCount };