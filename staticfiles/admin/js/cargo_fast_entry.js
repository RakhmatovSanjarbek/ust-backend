document.addEventListener('keydown', function(e) {
    if (e.key === 'Enter') {
        const activeElement = document.activeElement;

        // Faqat track_code inputida bo'lsak ishlaydi
        if (activeElement.name && activeElement.name.includes('track_code')) {
            e.preventDefault();

            const value = activeElement.value.trim();

            if (value !== "") {
                const inlineGroup = activeElement.closest('.inline-group');
                const addButton = inlineGroup.querySelector('.add-row a');
                const currentInput = activeElement; // Hozirgi inputni saqlab qolamiz

                if (addButton) {
                    // Yangi qator qo'shish tugmasini bosamiz
                    addButton.click();

                    // DOM o'zgarishlarini kuzatish
                    const observer = new MutationObserver(function(mutations) {
                        mutations.forEach(function(mutation) {
                            // Yangi qo'shilgan elementlarni tekshiramiz
                            if (mutation.addedNodes.length > 0) {
                                const allInputs = inlineGroup.querySelectorAll('input[name*="track_code"]');
                                const lastInput = allInputs[allInputs.length - 1];

                                // Agar yangi input topilsa va u eski inputdan farqli bo'lsa
                                if (lastInput && lastInput !== currentInput) {
                                    // Fokusni yangi inputga o'tkazamiz
                                    lastInput.focus();
                                    lastInput.value = ''; // Tozalaymiz (ixtiyoriy)

                                    // Kuzatishni to'xtatamiz
                                    observer.disconnect();
                                }
                            }
                        });
                    });

                    // Kuzatishni boshlaymiz
                    observer.observe(inlineGroup, {
                        childList: true,
                        subtree: true
                    });

                    // Xavfsizlik uchun 2 sekunddan keyin kuzatishni to'xtatamiz
                    setTimeout(() => {
                        observer.disconnect();
                    }, 2000);
                }
            }
        }
    }
});