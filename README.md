<h1 align="center">HotelsFinder </h1>
<h4 align="center">Ваш персональный помощник в поиске отеля в том или ином городе</h4>

<h2 align="center"> Что он умеет </h2>

 <h4><font color=red>/lowprice</font> - найдёт вам самые дешевые отели в городе, но готовьтесь к тому, что рейтинг  этих отелей будет не таким уж и высоким.</h4>
<h4><font color=red>/highprice</font> - найдёт самые дорогие отели в городе, высокие рейтинги отелей, но и высокие цены</h4>

<h4><font color=red>/bestdeal</font> - поиск лучших предложений которые только могут быть по указанным вами параметрам </h4>

<h4><font color=red>/history</font> - показывает ваши последние запросы по поиску отелей</h4>


<h2 align="center"> Описание функций</h2>
<h3 align="center"> /lowprice </h3>
Бот, принимает внешнюю команду /lowprice, запрашивает у пользователя название города, если отелей в указанном городе не найдено в базе данных Hotels.com, то пользователю будет предложено повторно ввести команду и повторить поиск города

При нахождении отелей, будет запрошено количество отелей для вывода, но не больше 10, если же количество отелей будет превышено, будет введено максимально допустимое число (10), если же пользователь ввёл не число, будет взято стандартное число отелей (5)

Дополнительно у пользователя запрашивается вывод фотографий отелей, если ответ положительный, то запрашивается количество фотографий (не больше 10), если ответ больше 10, то будет выведено 10 фотографий, если пользователь ошибся с вводом, будет выведено базовое значение (5)

Вывод отелей происходит по возрастанию цены за день проживания

<h3 align="center"> /highprice </h3>
Бот, принимает внешнюю команду /highprice, запрашивает у пользователя название города, если отелей в указанном городе не найдено в базе данных Hotels.com, то пользователю будет предложено повторно ввести команду и повторить поиск города

При нахождении отелей, будет запрошено количество отелей для вывода, но не больше 10, если же количество отелей будет превышено, будет введено максимально допустимое число (10), если же пользователь ввёл не число, будет взято стандартное число отелей (5)

Дополнительно у пользователя запрашивается вывод фотографий отелей, если ответ положительный, то запрашивается количество фотографий (не больше 10), если ответ больше 10, то будет выведено 10 фотографий, если пользователь ошибся с вводом, будет выведено базовое значение (5)

Вывод отелей происходит по убыванию цены за день проживания

<h3 align="center"> /bestdeal </h3>
Бот, принимает внешнюю команду /bestdeal, запрашивает у пользователя название города, если отелей в указанном городе не найдено в базе данных Hotels.com, то пользователю будет предложено повторно ввести команду и повторить поиск города

При нахождении отелей, будет запрошено количество отелей для вывода, но не больше 10, расстояние от центра  если же количество отелей будет превышено, будет введено максимально допустимое число (10), если же пользователь ввёл не число, будет взято стандартное число отелей (5)

Дополнительно у пользователя запрашивается вывод фотографий отелей, если ответ положительный, то запрашивается количество фотографий (не больше 10), если ответ больше 10, то будет выведено 10 фотографий, если пользователь ошибся с вводом, будет выведено базовое значение (5)

<h3 align="center"> /history </h3>
Бот, принимает внешнюю команду /history и выводит пользователю его последние 5 запросов у бота следующего формата: (дата, город, отели)