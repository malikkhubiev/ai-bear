<?php
// ai-bear/bot.php
// Полноценный Telegram-бот BAHUR на PHP

// --- Конфигурация ---
$TOKEN = getenv('TOKEN') ?: 'ВАШ_ТОКЕН';
$API_URL = "https://api.telegram.org/bot$TOKEN/";
$WEBHOOK_URL = getenv('WEBHOOK_BASE_URL') ?: 'https://your.domain/webhook';
$DEEPSEEK_KEY = getenv('DEEPSEEK_KEY');
$BAHUR_DATA = file_exists(__DIR__.'/bahur_data.txt') ? file_get_contents(__DIR__.'/bahur_data.txt') : '';
$USER_STATE_FILE = __DIR__.'/user_states.json';

// --- Состояния пользователей ---
function getUserStates() {
    global $USER_STATE_FILE;
    if (!file_exists($USER_STATE_FILE)) return [];
    $data = file_get_contents($USER_STATE_FILE);
    return $data ? json_decode($data, true) : [];
}
function setUserStates($states) {
    global $USER_STATE_FILE;
    file_put_contents($USER_STATE_FILE, json_encode($states));
}
function setUserState($user_id, $state) {
    $states = getUserStates();
    if ($state) $states[$user_id] = $state;
    else unset($states[$user_id]);
    setUserStates($states);
}
function getUserState($user_id) {
    $states = getUserStates();
    return $states[$user_id] ?? null;
}

// --- Вспомогательные функции ---
function sendMessage($chat_id, $text, $reply_markup = null, $parse_mode = 'HTML') {
    global $API_URL;
    $data = [
        'chat_id' => $chat_id,
        'text' => $text,
        'parse_mode' => $parse_mode
    ];
    if ($reply_markup) {
        $data['reply_markup'] = json_encode($reply_markup);
    }
    file_get_contents($API_URL . 'sendMessage?' . http_build_query($data));
}

function editMessage($chat_id, $message_id, $text, $reply_markup = null, $parse_mode = 'HTML') {
    global $API_URL;
    $data = [
        'chat_id' => $chat_id,
        'message_id' => $message_id,
        'text' => $text,
        'parse_mode' => $parse_mode
    ];
    if ($reply_markup) {
        $data['reply_markup'] = json_encode($reply_markup);
    }
    file_get_contents($API_URL . 'editMessageText?' . http_build_query($data));
}

function answerCallbackQuery($callback_query_id) {
    global $API_URL;
    file_get_contents($API_URL . 'answerCallbackQuery?callback_query_id=' . $callback_query_id);
}

function searchNoteApi($note) {
    $url = "https://api.alexander-dev.ru/bahur/search/?text=" . urlencode($note);
    $response = file_get_contents($url);
    return json_decode($response, true);
}

function searchByIdApi($id) {
    $url = "https://api.alexander-dev.ru/bahur/search/?id=" . urlencode($id);
    $response = file_get_contents($url);
    return json_decode($response, true);
}

function askDeepseek($question, $bahur_data) {
    global $DEEPSEEK_KEY;
    $url = 'https://api.deepseek.com/v1/chat/completions';
    $headers = [
        'Authorization: Bearer ' . $DEEPSEEK_KEY,
        'Content-Type: application/json'
    ];
    $data = [
        'model' => 'deepseek-chat',
        'messages' => [
            [
                'role' => 'system',
                'content' => "Ты - Ai-Медвежонок (менеджер по продажам), здоровайся креативно, зная это. Используй ТОЛЬКО эти данные для ответа клиенту:\n"
                    . $bahur_data . "\nЕсли есть подходящая ссылка из данных, обязательно включи её в ответ. Отвечай только по теме вопроса, без лишней информации, на русском языке, без markdown, обязательно с крутыми смайликами. Если вопрос не по теме, то обязательно переведи в шутку, никаких 'не знаю' и аккуратно предложи купить духи Когда вставляешь ссылку, используй HTML-формат: <a href='ССЫЛКА'>ТЕКСТ</a>. Не используй markdown. Но если он пишет несколько слов, которые похожи на ноты, предложи ему нажать на кнопку 🍓 Ноты в меню Не пиши про номера ароматов в прайсе"
            ],
            [
                'role' => 'user',
                'content' => $question
            ]
        ],
        'temperature' => 0.9
    ];
    $ch = curl_init($url);
    curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    curl_setopt($ch, CURLOPT_POST, 1);
    curl_setopt($ch, CURLOPT_POSTFIELDS, json_encode($data));
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    curl_setopt($ch, CURLOPT_TIMEOUT, 30);
    $result = curl_exec($ch);
    curl_close($ch);
    $json = json_decode($result, true);
    return $json['choices'][0]['message']['content'] ?? 'Ошибка AI';
}

// --- Основная логика ---
$content = file_get_contents("php://input");
$update = json_decode($content, true);
if (!$update) exit;

if (isset($update['message'])) {
    $message = $update['message'];
    $chat_id = $message['chat']['id'];
    $user_id = $message['from']['id'];
    $text = trim($message['text'] ?? '');
    $state = getUserState($user_id);

    // Команда /start
    if ($text === '/start') {
        $main_menu = [
            'inline_keyboard' => [
                [ ['text' => '🧸 Ai-Медвежонок', 'callback_data' => 'ai'] ],
                [
                    ['text' => '🍦 Прайс', 'url' => 'https://drive.google.com/file/d/1J70LlZwh6g7JOryDG2br-weQrYfv6zTc/view?usp=sharing'],
                    ['text' => '🍿 Магазин', 'url' => 'https://www.bahur.store/m/'],
                    ['text' => '♾️ Вопросы', 'url' => 'https://vk.com/@bahur_store-optovye-praisy-ot-bahur']
                ],
                [
                    ['text' => '🎮 Чат', 'url' => 'https://t.me/+VYDZEvbp1pce4KeT'],
                    ['text' => '💎 Статьи', 'url' => 'https://vk.com/bahur_store?w=app6326142_-133936126%2523w%253Dapp6326142_-133936126'],
                    ['text' => '🏆 Отзывы', 'url' => 'https://vk.com/@bahur_store']
                ],
                [ ['text' => '🍓 Ноты', 'callback_data' => 'instruction'] ]
            ]
        ];
        sendMessage($chat_id, "<b>Здравствуйте!\n\nЯ — ваш ароматный помощник от BAHUR.\n🍓 Ищу ноты и 🧸 отвечаю на вопросы с любовью. ❤</b>", $main_menu);
        setUserState($user_id, null);
        exit;
    }

    // AI-режим
    if ($state === 'awaiting_ai_question') {
        $ai_answer = askDeepseek($text, $BAHUR_DATA);
        // Удаляем markdown-символы и некорректные <a> теги
        $ai_answer = preg_replace('/[\*_~`>#\[\]\(\)!\-]/u', '', $ai_answer);
        $ai_answer = preg_replace('/<a\s+href=["\']{0,1}[\s"\']{0,1}>.*?<\/a>/u', '', $ai_answer);
        $ai_answer = preg_replace('/<a\s*>.*?<\/a>/u', '', $ai_answer);
        sendMessage($chat_id, $ai_answer);
        setUserState($user_id, null);
        exit;
    }

    // Режим поиска нот
    if ($state === 'awaiting_note_search') {
        $result = searchNoteApi($text);
        if ($result && $result['status'] === 'success') {
            $brand = $result['brand'];
            $aroma = $result['aroma'];
            $description = $result['description'];
            $url = $result['url'];
            $aroma_id = $result['ID'];
            $reply_markup = [
                'inline_keyboard' => [
                    [
                        ['text' => '🚀 Подробнее', 'url' => $url],
                        ['text' => '♾️ Повторить', 'callback_data' => 'repeatapi_' . $aroma_id]
                    ]
                ]
            ];
            sendMessage($chat_id, "✨ $brand $aroma\n\n$description", $reply_markup);
        } else {
            sendMessage($chat_id, "Ничего не найдено по этой ноте 😢");
        }
        setUserState($user_id, null);
        exit;
    }

    // Обычный текст — предлагаем выбрать режим
    $main_menu = [
        'inline_keyboard' => [
            [ ['text' => '🧸 Ai-Медвежонок', 'callback_data' => 'ai'] ],
            [ ['text' => '🍓 Ноты', 'callback_data' => 'instruction'] ]
        ]
    ];
    sendMessage($chat_id, "Выберите режим: 🧸 Ai-Медвежонок или 🍓 Ноты", $main_menu);
    exit;
}

if (isset($update['callback_query'])) {
    $callback = $update['callback_query'];
    $data = $callback['data'];
    $chat_id = $callback['message']['chat']['id'];
    $user_id = $callback['from']['id'];
    $message_id = $callback['message']['message_id'];
    $callback_id = $callback['id'];

    if ($data === 'instruction') {
        setUserState($user_id, 'awaiting_note_search');
        editMessage($chat_id, $message_id, '🍉 Напиши любую ноту (например, апельсин, клубника) — я найду ароматы с этой нотой!');
        answerCallbackQuery($callback_id);
        exit;
    }
    if ($data === 'ai') {
        setUserState($user_id, 'awaiting_ai_question');
        editMessage($chat_id, $message_id, 'Привет-привет! 🐾 Готов раскрыть все секреты продаж — спрашивай смело!');
        answerCallbackQuery($callback_id);
        exit;
    }
    if (strpos($data, 'repeatapi_') === 0) {
        $aroma_id = substr($data, strlen('repeatapi_'));
        $result = searchByIdApi($aroma_id);
        if ($result && $result['status'] === 'success') {
            $brand = $result['brand'];
            $aroma = $result['aroma'];
            $description = $result['description'];
            $url = $result['url'];
            $aroma_id = $result['ID'];
            $reply_markup = [
                'inline_keyboard' => [
                    [
                        ['text' => '🚀 Подробнее', 'url' => $url],
                        ['text' => '♾️ Повторить', 'callback_data' => 'repeatapi_' . $aroma_id]
                    ]
                ]
            ];
            editMessage($chat_id, $message_id, "✨ $brand $aroma\n\n$description", $reply_markup);
        } else {
            editMessage($chat_id, $message_id, "Ничего не найдено по этой ноте 😢");
        }
        answerCallbackQuery($callback_id);
        exit;
    }
}

// Healthcheck endpoint
if (isset($_GET['healthcheck'])) {
    echo 'OK';
    exit;
} 