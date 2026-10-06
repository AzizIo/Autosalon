INSERT INTO Dealerships (address, city, phone_number) VALUES
 ('ул. Тверская, 10', 'Москва', '+7 495 100-10-10'),
 ('Невский пр., 45', 'Санкт-Петербург', '+7 812 200-20-20'),
 ('ул. Баумана, 7', 'Казань', '+7 843 300-30-30');

INSERT INTO Manufacturers (manufacturer_name, country) VALUES
 ('Toyota', 'Япония'), ('Volkswagen', 'Германия'), ('Kia', 'Южная Корея'),
 ('Skoda', 'Чехия'), ('BMW', 'Германия'), ('Haval', 'Китай');

INSERT INTO Cars (model_name, price, year_of_manufacture, body_type, color, manufacturer_id) VALUES
 ('Toyota Camry', 3250000, 2024, 'Седан', 'Чёрный', 1),
 ('Toyota RAV4', 3890000, 2024, 'Кроссовер', 'Белый', 1),
 ('Volkswagen Polo', 1650000, 2023, 'Седан', 'Серебристый', 2),
 ('Volkswagen Tiguan', 3480000, 2024, 'Кроссовер', 'Серый', 2),
 ('Kia Rio', 1590000, 2023, 'Седан', 'Синий', 3),
 ('Kia Sportage', 3150000, 2024, 'Кроссовер', 'Красный', 3),
 ('Skoda Octavia', 2650000, 2023, 'Лифтбек', 'Белый', 4),
 ('BMW 3 Series', 5400000, 2024, 'Седан', 'Чёрный', 5),
 ('Haval Jolion', 2150000, 2024, 'Кроссовер', 'Зелёный', 6),
 ('Haval H9', 3790000, 2023, 'Внедорожник', 'Серый', 6);

INSERT INTO Customers (first_name, last_name, email, phone_number) VALUES
 ('Иван', 'Петров', 'petrov@example.com', '+7 900 111-11-11'),
 ('Анна', 'Смирнова', 'smirnova@example.com', '+7 900 222-22-22'),
 ('Олег', 'Кузнецов', 'kuznetsov@example.com', '+7 900 333-33-33');

INSERT INTO Employees (first_name, last_name, phone_number, job_title, dealership_id) VALUES
 ('Мария', 'Орлова', '+7 901 000-00-01', 'Менеджер по продажам', 1),
 ('Денис', 'Волков', '+7 901 000-00-02', 'Менеджер по продажам', 1),
 ('Елена', 'Зайцева', '+7 901 000-00-03', 'Менеджер по продажам', 2),
 ('Артём', 'Никитин', '+7 901 000-00-04', 'Старший менеджер', 3);

INSERT INTO Stock (dealership_id, car_id, car_count) VALUES
 (1,1,3),(1,2,2),(1,3,5),(1,4,2),(1,5,4),(1,8,1),
 (2,1,1),(2,3,3),(2,6,2),(2,7,4),(2,9,3),
 (3,2,1),(3,5,6),(3,7,2),(3,9,2),(3,10,1);
