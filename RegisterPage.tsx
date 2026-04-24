import { useState } from 'react';

interface RegisterPageProps {
    onRegister: (userData: any) => void;
}

function RegisterPage({ onRegister }: RegisterPageProps) {
    const [formData, setFormData] = useState({
        name: '',
        email: '',
        password: '',
        age: '',
        city: ''
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        // Пока просто передаём данные наверх
        onRegister({
            ...formData,
            age: parseInt(formData.age)
        });
    };

    return (
        <div style={{
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center',
            minHeight: '100vh',
            backgroundColor: '#f5f5f5'
        }}>
            <form onSubmit={handleSubmit} style={{
                backgroundColor: 'white',
                padding: '40px',
                borderRadius: '20px',
                boxShadow: '0 4px 15px rgba(0,0,0,0.1)',
                width: '400px'
            }}>
                <h1 style={{ textAlign: 'center', color: '#ff6b6b', marginBottom: '30px' }}>
                    Регистрация
                </h1>
                
                <input
                    type="text"
                    placeholder="Имя"
                    value={formData.name}
                    onChange={(e) => setFormData({...formData, name: e.target.value})}
                    required
                    style={inputStyle}
                />
                
                <input
                    type="email"
                    placeholder="Email"
                    value={formData.email}
                    onChange={(e) => setFormData({...formData, email: e.target.value})}
                    required
                    style={inputStyle}
                />
                
                <input
                    type="password"
                    placeholder="Пароль"
                    value={formData.password}
                    onChange={(e) => setFormData({...formData, password: e.target.value})}
                    required
                    style={inputStyle}
                />
                
                <input
                    type="number"
                    placeholder="Возраст"
                    value={formData.age}
                    onChange={(e) => setFormData({...formData, age: e.target.value})}
                    required
                    style={inputStyle}
                />
                
                <input
                    type="text"
                    placeholder="Город"
                    value={formData.city}
                    onChange={(e) => setFormData({...formData, city: e.target.value})}
                    required
                    style={inputStyle}
                />
                
                <button type="submit" style={{
                    ...inputStyle,
                    backgroundColor: '#ff6b6b',
                    color: 'white',
                    border: 'none',
                    cursor: 'pointer',
                    fontSize: '16px',
                    fontWeight: 'bold'
                }}>
                    Зарегистрироваться
                </button>
            </form>
        </div>
    );
}

const inputStyle = {
    width: '100%',
    padding: '12px',
    marginBottom: '15px',
    border: '1px solid #ddd',
    borderRadius: '8px',
    fontSize: '14px',
    boxSizing: 'border-box' as const
};

export default RegisterPage;