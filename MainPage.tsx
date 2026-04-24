import { useState } from 'react';
import Navbar from '../components/Navbar';
import UserCard from '../components/UserCard';
import { mockUsers, currentUser } from '../services/mockData';

function MainPage({ user }) {
    const [activeTab, setActiveTab] = useState('candidates');
    const [selectedUser, setSelectedUser] = useState(null);
    const [favorites, setFavorites] = useState([]);
    const [comments, setComments] = useState({});
    const [newComment, setNewComment] = useState('');

    const candidates = mockUsers.filter(u => u.id !== user.id);
    const favoriteUsers = candidates.filter(u => favorites.includes(u.id));

    // Функция для избранного
    const handleAddToFavorites = (userId) => {
        console.log('handleAddToFavorites вызвана, userId:', userId);
        console.log('Текущие избранные:', favorites);
        
        if (favorites.includes(userId)) {
            console.log('Удаляем из избранного');
            setFavorites(favorites.filter(id => id !== userId));
        } else {
            console.log('Добавляем в избранное');
            setFavorites([...favorites, userId]);
        }
    };

    // Функция добавления комментария
    const handleAddComment = (userId) => {
        if (newComment.trim() === '') return;
        
        const newCommentObj = {
            id: Date.now(),
            author: user.name,
            authorId: user.id,
            text: newComment,
            date: new Date().toLocaleString()
        };
        
        setComments(prev => ({
            ...prev,
            [userId]: [...(prev[userId] || []), newCommentObj]
        }));
        
        setNewComment('');
    };

    const handleDeleteComment = (userId, commentId) => {
        setComments(prev => ({
            ...prev,
            [userId]: prev[userId].filter(c => c.id !== commentId)
        }));
    };

    // Детальный просмотр пользователя
    if (selectedUser) {
        const userComments = comments[selectedUser.id] || [];
        
        return (
            <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
                <button 
                    onClick={() => setSelectedUser(null)}
                    style={{
                        backgroundColor: '#ff6b6b',
                        color: 'white',
                        border: 'none',
                        padding: '10px 20px',
                        borderRadius: '8px',
                        cursor: 'pointer',
                        marginBottom: '20px'
                    }}
                >
                    ← Назад к списку
                </button>
                
                <div style={{
                    backgroundColor: 'white',
                    borderRadius: '20px',
                    padding: '30px',
                    boxShadow: '0 4px 15px rgba(0,0,0,0.1)',
                    marginBottom: '30px'
                }}>
                    <img 
                        src={selectedUser.photo} 
                        alt={selectedUser.name}
                        style={{
                            width: '100%',
                            maxHeight: '400px',
                            objectFit: 'cover',
                            borderRadius: '15px'
                        }}
                    />
                    <h1>{selectedUser.name}, {selectedUser.age} лет</h1>
                    <p>📍 {selectedUser.city}</p>
                    <h3>О себе:</h3>
                    <p>{selectedUser.description}</p>
                    <h3>Интересы:</h3>
                    <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
                        {selectedUser.interests.map((interest, i) => (
                            <span key={i} style={{
                                backgroundColor: '#ff6b6b',
                                color: 'white',
                                padding: '5px 15px',
                                borderRadius: '20px'
                            }}>
                                {interest}
                            </span>
                        ))}
                    </div>
                    
                    <button 
                        onClick={() => handleAddToFavorites(selectedUser.id)}
                        style={{
                            marginTop: '20px',
                            backgroundColor: favorites.includes(selectedUser.id) ? '#ff6b6b' : '#4CAF50',
                            color: 'white',
                            border: 'none',
                            padding: '12px 24px',
                            borderRadius: '25px',
                            cursor: 'pointer',
                            fontSize: '16px'
                        }}
                    >
                        {favorites.includes(selectedUser.id) ? '⭐ В избранном' : '🤍 Добавить в избранное'}
                    </button>
                </div>

                {/* Блок комментариев */}
                <div style={{
                    backgroundColor: 'white',
                    borderRadius: '20px',
                    padding: '30px',
                    boxShadow: '0 4px 15px rgba(0,0,0,0.1)'
                }}>
                    <h3>💬 Отзывы о {selectedUser.name}</h3>
                    
                    <div style={{ marginBottom: '30px' }}>
                        <textarea
                            value={newComment}
                            onChange={(e) => setNewComment(e.target.value)}
                            placeholder="Напишите ваш отзыв о кандидате..."
                            style={{
                                width: '100%',
                                padding: '12px',
                                borderRadius: '10px',
                                border: '1px solid #ddd',
                                fontSize: '14px',
                                fontFamily: 'inherit',
                                resize: 'vertical',
                                minHeight: '80px',
                                boxSizing: 'border-box'
                            }}
                        />
                        <button
                            onClick={() => handleAddComment(selectedUser.id)}
                            style={{
                                marginTop: '10px',
                                backgroundColor: '#4CAF50',
                                color: 'white',
                                border: 'none',
                                padding: '10px 20px',
                                borderRadius: '25px',
                                cursor: 'pointer',
                                fontSize: '14px'
                            }}
                        >
                            📝 Отправить отзыв
                        </button>
                    </div>

                    <div style={{ maxHeight: '400px', overflowY: 'auto' }}>
                        {userComments.length === 0 ? (
                            <p style={{ color: '#999', textAlign: 'center', padding: '20px' }}>
                                Пока нет отзывов. Будьте первым!
                            </p>
                        ) : (
                            userComments.map(comment => (
                                <div key={comment.id} style={{
                                    borderBottom: '1px solid #eee',
                                    padding: '15px 0',
                                    marginBottom: '10px'
                                }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                                        <strong style={{ color: '#ff6b6b' }}>{comment.author}</strong>
                                        <span style={{ fontSize: '12px', color: '#999' }}>{comment.date}</span>
                                    </div>
                                    <p style={{ margin: '0 0 8px 0', lineHeight: '1.4' }}>{comment.text}</p>
                                    {comment.authorId === user.id && (
                                        <button
                                            onClick={() => handleDeleteComment(selectedUser.id, comment.id)}
                                            style={{
                                                backgroundColor: 'transparent',
                                                color: '#ff6b6b',
                                                border: 'none',
                                                fontSize: '12px',
                                                cursor: 'pointer',
                                                padding: '0'
                                            }}
                                        >
                                            🗑️ Удалить
                                        </button>
                                    )}
                                </div>
                            ))
                        )}
                    </div>
                </div>
            </div>
        );
    }

    const renderContent = () => {
        switch (activeTab) {
            case 'profile':
                return (
                    <div style={{
                        backgroundColor: 'white',
                        borderRadius: '20px',
                        padding: '30px',
                        maxWidth: '600px',
                        margin: '0 auto'
                    }}>
                        <h2>Мой профиль</h2>
                        <img 
                            src={user.photo} 
                            alt={user.name}
                            style={{
                                width: '150px',
                                height: '150px',
                                borderRadius: '50%',
                                objectFit: 'cover'
                            }}
                        />
                        <p><strong>Имя:</strong> {user.name}</p>
                        <p><strong>Email:</strong> {user.email}</p>
                        <p><strong>Возраст:</strong> {user.age}</p>
                        <p><strong>Город:</strong> {user.city}</p>
                    </div>
                );
            
            case 'favorites':
                return (
                    <div>
                        <h2>Избранное ({favoriteUsers.length})</h2>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '20px', justifyContent: 'center' }}>
                            {favoriteUsers.map(user => (
                                <UserCard 
                                    key={user.id} 
                                    user={user} 
                                    onClick={() => setSelectedUser(user)}
                                />
                            ))}
                        </div>
                        {favoriteUsers.length === 0 && (
                            <p style={{ textAlign: 'center', color: '#999' }}>
                                Пока нет избранных. Добавьте кого-нибудь из кандидатов!
                            </p>
                        )}
                    </div>
                );
            
            case 'candidates':
            default:
                return (
                    <div>
                        <h2>Кандидаты ({candidates.length})</h2>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '20px', justifyContent: 'center' }}>
                            {candidates.map(candidate => (
                                <UserCard 
                                    key={candidate.id} 
                                    user={candidate} 
                                    onClick={() => setSelectedUser(candidate)}
                                />
                            ))}
                        </div>
                    </div>
                );
        }
    };

    return (
        <div style={{ padding: '20px', maxWidth: '1200px', margin: '0 auto' }}>
            <Navbar activeTab={activeTab} onTabChange={setActiveTab} />
            {renderContent()}
        </div>
    );
}

export default MainPage;