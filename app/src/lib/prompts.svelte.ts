import { browser } from "$app/environment";
import { type BootstrapColor } from "./colors/color";
import Modal from "./components/Modal.svelte";
import { createRawSnippet, mount } from "svelte";

const target = (() => {
    if (browser) {
        const target = document.createElement("div");
        document.body.appendChild(target);
        return target;
    }
    return null;
})();

type ButtonConfig = {
    text: string;
    color: BootstrapColor;
    onClick: () => void;
};
const createButton = (config: ButtonConfig) => {
    //  onclick="${config.onClick}"
    return createRawSnippet(() => ({
        render: () => `<button class="btn btn-${config.color}">${config.text}</button>`,
        setup: (el) => {
            el.addEventListener("click", config.onClick);
        }
    }));
};

const createButtons = (buttons: ButtonConfig[]) => {
    return createRawSnippet(() => ({
        render: () => `<div>${buttons.map((button, i) => `<button data-id=${i} class="btn btn-${button.color}">${button.text}</button>`).join("")}</div>`,
        setup: (el) => {
            for (let i = 0; i < buttons.length; i++) {
                el.children[i]?.addEventListener("click", buttons[i].onClick);
            }
        }
    }));
}

const createModalBody = (message: string) => createRawSnippet(() => ({
    render: () => `<p>${message}</p>`,
}));


type PromptConfig = {
    title?: string;
    password?: boolean;
    placeholder?: string;
    multiline?: boolean;
    validate?: (value: string) => boolean;
};
export const prompt = async (message: string, config?: PromptConfig) => {
    return new Promise<string | null>((res, rej) => {
        if (!target) return rej("Cannot show prompt in non-browser environment");

        let value = "";
        let valid = true;

        const modal = mount(Modal, {
            target,
            props: {
                title: config?.title || "Prompt",
                body: createRawSnippet(() => ({
                    render: () => `
                        <div>
                            <p>${message}</p>
                            ${
                                config?.multiline
                                    ? `<textarea data-id="input" class="form-control" placeholder="${config?.placeholder || ""}"></textarea>`
                                    : `<input data-id="input" type="${config?.password ? "password" : "text"}" class="form-control" placeholder="${config?.placeholder || ""}">`
                            }
                        </div>
                    `,
                    setup: (el) => {
                        const input = el.querySelector("input") || el.querySelector("textarea");
                        input?.addEventListener("input", (e) => {
                            value = (e.target as HTMLInputElement).value;
                            valid = !config?.validate || config.validate(value);
                            input.classList.toggle("is-invalid", !valid);
                        });
                    }
                })),
                buttons: createButtons([
                    {
                        text: "Cancel",
                        color: "secondary",
                        onClick: () => {
                            modal.hide();
                            res(null);
                        }
                    },
                    {
                        text: "Ok",
                        color: "primary",
                        onClick: () => {
                            if (!valid) return;
                            modal.hide();
                            res(value);
                        }
                    }
                ])
            }
        });

        modal.show();

        modal.on('hide', () => res(null));
    });
};

type SelectConfig<T> = {
    title?: string;
    render?: (value: T) => string;
};
export const select = async <T>(message: string, options: T[], config?: SelectConfig<T>) => {
    return new Promise<T | null>((res, rej) => {
        if (!target) return rej("Cannot show select in non-browser environment");

        let selected: T | null = null;

        const modal = mount(Modal, {
            target,
            props: {
                title: config?.title || "Select",
                body: createRawSnippet(() => ({
                    render: () => `
                        <div>
                            <p>${message}</p>
                            <select class="form-select" data-id="select">
                                <option disabled selected>Select an option</option>
                                ${
                                    options.map((option, i) => {
                                        return `<option value="${i}">${config?.render ? config.render(option) : option}</option>`;
                                    })
                                }
                            </select>
                        </div>
                    `,
                    setup: (el) => {
                        el.querySelector("select")?.addEventListener("change", (e) => {
                            selected = options[parseInt((e.target as HTMLSelectElement).value)];
                        });
                    }
                })),
                buttons: createButtons([
                    {
                        text: "Cancel",
                        color: "secondary",
                        onClick: () => {
                            modal.hide();
                            res(null);
                        }
                    },
                    {
                        text: 'Select',
                        color: "primary",
                        onClick: () => {
                            modal.hide();
                            res(selected);
                        }
                    }
                ])
            }
        });

        modal.show();
    });
}

type ChooseConfig<A, B> = {
    title?: string;
    renderA?: (value: A) => string;
    renderB?: (value: B) => string;
}
export const choose = async <A, B>(message: string, A: A, B: B, config?: ChooseConfig<A, B>) => {
    return new Promise<boolean | null>((res, rej) => {
        if (!target) return rej("Cannot show choose in non-browser environment");

        const modal = mount(Modal, {
            target,
            props: {
                title: config?.title || "Choose",
                body: createModalBody(message),
                buttons: createButtons([
                    {
                        text: "Cancel",
                        color: "secondary",
                        onClick: () => {
                            modal.hide();
                            res(null);
                        }
                    },
                    {
                        text: config?.renderA ? config.renderA(A) : "A",
                        color: "primary",
                        onClick: () => {
                            modal.hide();
                            res(true);
                        }
                    },
                    {
                        text: config?.renderB ? config.renderB(B) : "B",
                        color: "primary",
                        onClick: () => {
                            modal.hide();
                            res(false);
                        }
                    }
                ]),
            }
        });
        modal.show();

        modal.on('hide', () => res(false));
    });
};


type ConfirmConfig = {
    title?: string;
    yes?: string;
    no?: string;
};
export const confirm = async (message: string, config?: ConfirmConfig) => {
    return new Promise<boolean>((res, rej) => {
        if (!target) return rej("Cannot show confirm in non-browser environment");

        const modal = mount(Modal, {
            target,
            props: {
                title: config?.title || "Confirm",
                body: createModalBody(message),
                buttons: createButtons([
                    {
                        text: config?.yes || "Yes",
                        color: "success",
                        onClick: () => {
                            modal.hide();
                            res(true);
                        }
                    },
                    {
                        text: config?.no || "No",
                        color: "danger",
                        onClick: () => {
                            modal.hide();
                            res(false);
                        }
                    }
                ]),
            }
        });
        modal.show();

        modal.on('hide', () => res(false));
    });
};


type AlertConfig = {
    title?: string;
}
export const alert = async (message: string, config?: AlertConfig) => {
    return new Promise<void>((res, rej) => {
        if (!target) return rej("Cannot show alert in non-browser environment");
    
        const modal = mount(Modal, {
            target,
            props: {
                title: config?.title || "Alert",
                body: createModalBody(message),
                buttons: createButton({
                    text: "Ok",
                    color: "primary",
                    onClick: () => {
                        modal.hide();
                        res();
                    },
                }),
            }
        });
        modal.show();

        modal.on('hide', () => res());
    });
};

type ColorPickerConfig = {
    title?: string;
}
export const colorPicker = async (message: string, config?: ColorPickerConfig) => {
    return new Promise<string | null>((res, rej) => {
        if (!target) return rej("Cannot show color picker in non-browser environment");

        let selected: string | null = null;

        const modal = mount(Modal, {
            target,
            props: {
                title: config?.title || "Color Picker",
                body: createRawSnippet(() => ({
                    render: () => `
                        <div>
                            <p>${message}</p>
                            <input type="color" class="form-control" data-id="color">
                        </div>
                    `,
                    setup: (el) => {
                        el.querySelector("input")?.addEventListener("input", (e) => {
                            selected = (e.target as HTMLInputElement).value;
                        });
                    }
                })),
                buttons: createButtons([
                    {
                        text: "Cancel",
                        color: "secondary",
                        onClick: () => {
                            modal.hide();
                            res(null);
                        }
                    },
                    {
                        text: "Select",
                        color: "primary",
                        onClick: () => {
                            modal.hide();
                            res(selected as string);
                        }
                    }
                ])
            }
        });

        modal.show();
    });
}