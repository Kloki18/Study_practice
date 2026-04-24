// Список фейковых пользователей (кандидатов)

export const mockUsers = [
    {
        id: 1,
        name: 'Анна',
        age: 25,
        city: 'Москва',
        photo: 'https://randomuser.me/api/portraits/women/1.jpg',
        description: 'Люблю путешествия, кофе и долгие прогулки. Ищу серьёзные отношения.',
        interests: ['путешествия', 'фотография', 'йога']
    },
    {
        id: 2,
        name: 'Дмитрий',
        age: 28,
        city: 'Санкт-Петербург',
        photo: 'https://randomuser.me/api/portraits/men/2.jpg',
        description: 'Разработчик, в свободное время играю на гитаре. Хочу создать семью.',
        interests: ['музыка', 'программирование', 'спорт']
    },
    {
        id: 3,
        name: 'Екатерина',
        age: 23,
        city: 'Казань',
        photo: 'https://randomuser.me/api/portraits/women/3.jpg',
        description: 'Люблю читать книги и учить новое. Ищу умного и доброго человека.',
        interests: ['чтение', 'танцы', 'кулинария']
    },
    {
        id: 4,
        name: 'Максим',
        age: 31,
        city: 'Новосибирск',
        photo: 'https://randomuser.me/api/portraits/men/4.jpg',
        description: 'Спортсмен, люблю активный отдых. Жду свою вторую половинку.',
        interests: ['футбол', 'путешествия', 'рыбалка']
    }
];

// Текущий пользователь (кто залогинен)
export const currentUser = {
    id: 999,
    name: 'Алиса',
    email: 'alisa@example.com',
    age: 24,
    city: 'Москва',
    photo: 'https://randomuser.me/api/portraits/women/90.jpg'
};