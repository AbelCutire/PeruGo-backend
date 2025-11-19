import { Router } from "express";
import { PrismaClient } from "@prisma/client";
import bcrypt from "bcrypt";
import jwt from "jsonwebtoken";

const prisma = new PrismaClient();
const router = Router();

// LOGIN
router.post("/login", async (req, res) => {
  const { email, username, password } = req.body;

  if (!email || !username || !password)
    return res.status(400).json({ error: "Faltan datos" });

  const user = await prisma.user.findUnique({ where: { email } });
  if (!user) return res.status(404).json({ error: "Usuario no existe" });

  if (user.username !== username)
    return res.status(400).json({ error: "Usuario incorrecto" });

  const ok = await bcrypt.compare(password, user.password);
  if (!ok) return res.status(401).json({ error: "Contraseña incorrecta" });

  const token = jwt.sign({ id: user.id }, process.env.JWT_SECRET, {
    expiresIn: "7d",
  });

  res.json({ token });
});

// REGISTER
router.post("/register", async (req, res) => {
  const { email, username, password } = req.body;

  const exists = await prisma.user.findUnique({ where: { email } });
  if (exists) return res.status(400).json({ error: "Correo ya existe" });

  const hash = await bcrypt.hash(password, 10);

  const user = await prisma.user.create({
    data: { email, username, password: hash },
  });

  res.json({ id: user.id });
});

// RECOVER
router.post("/recover", async (req, res) => {
  const { email } = req.body;
  if (!email) return res.status(400).json({ error: "Correo requerido" });

  const user = await prisma.user.findUnique({ where: { email } });
  if (!user) return res.status(404).json({ error: "Correo no existe" });

  // Aquí solo devolvemos OK.  
  // Usted puede añadir envío de correo si lo desea.
  res.json({ message: "Correo enviado (simulado)" });
});

export default router;
