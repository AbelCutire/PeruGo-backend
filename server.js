const express = require('express');
const cors = require('cors');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');

// Inicializar Prisma con manejo de errores
let prisma;
try {
  const { PrismaClient } = require('@prisma/client');
  prisma = new PrismaClient();
  console.log('✅ Prisma client initialized successfully');
} catch (error) {
  console.error('❌ Failed to initialize Prisma client:', error.message);
  console.log('💡 Run: npx prisma generate');
  process.exit(1);
}

const app = express();
const PORT = process.env.PORT || 5000;
const JWT_SECRET = process.env.JWT_SECRET || 'fallback-secret-key-2024';

// Middleware
app.use(cors({
  origin: '*',
  methods: ['GET', 'POST', 'PUT', 'DELETE'],
  credentials: true
}));

app.use(express.json());

// Ruta de prueba principal
app.get('/', (req, res) => {
  res.json({ 
    message: 'Servidor backend operativo.',
    status: 'online',
    timestamp: new Date().toISOString(),
    database: prisma ? 'connected' : 'disconnected'
  });
});

// Ruta de status
app.get('/auth/status', (req, res) => {
  res.json({ 
    message: 'Rutas de autenticación operativas',
    status: 'active',
    database: prisma ? 'connected' : 'disconnected',
    routes: [
      'POST /auth/login',
      'POST /auth/register', 
      'POST /auth/recover'
    ]
  });
});

// Ruta de login
app.post('/auth/login', async (req, res) => {
  try {
    if (!prisma) {
      return res.status(500).json({ error: 'Database not available' });
    }
    
    console.log('📨 Login request:', req.body);
    const { email, password } = req.body;

    if (!email || !password) {
      return res.status(400).json({ error: 'Email y contraseña son requeridos' });
    }

    const user = await prisma.user.findUnique({ where: { email } });

    if (!user) {
      return res.status(400).json({ error: 'Usuario no encontrado' });
    }

    const isPasswordValid = await bcrypt.compare(password, user.password);
    if (!isPasswordValid) {
      return res.status(400).json({ error: 'Contraseña incorrecta' });
    }

    const token = jwt.sign(
      { userId: user.id, email: user.email },
      JWT_SECRET,
      { expiresIn: '24h' }
    );

    res.json({
      message: 'Login exitoso',
      token,
      user: {
        id: user.id,
        email: user.email,
        username: user.username
      }
    });

  } catch (error) {
    console.error('❌ Error en login:', error);
    res.status(500).json({ error: 'Error interno del servidor' });
  }
});

// ... (las otras rutas similares con verificación de prisma)

// Manejo de cierre graceful
process.on('SIGINT', async () => {
  if (prisma) {
    await prisma.$disconnect();
  }
  process.exit(0);
});

app.listen(PORT, '0.0.0.0', () => {
  console.log(`🚀 Servidor corriendo en puerto ${PORT}`);
  console.log('✅ Prisma client:', prisma ? 'Connected' : 'Disconnected');
});