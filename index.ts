export interface IUser {
    id: number;
    name: string;
    age: number;
    city: string;
    photo: string;
    description: string;
    interests: string[];
}

export interface IRegisterData {
    name: string;
    email: string;
    password: string;
    age: number;
    city: string;
}