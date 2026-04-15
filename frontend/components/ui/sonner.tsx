"use client";
import { Toaster as Sonner } from "sonner";

type ToasterProps = React.ComponentProps<typeof Sonner>;

export function Toaster({ ...props }: ToasterProps) {
  return (
    <Sonner
      theme="dark"
      className="toaster group"
      toastOptions={{
        classNames: {
          toast:
            "group toast group-[.toaster]:bg-[#0d0e1a] group-[.toaster]:text-white group-[.toaster]:border-white/10 group-[.toaster]:shadow-lg",
          description: "group-[.toast]:text-white/60",
          actionButton: "group-[.toast]:bg-[#f97316] group-[.toast]:text-black",
          cancelButton: "group-[.toast]:bg-white/10 group-[.toast]:text-white/60",
        },
      }}
      {...props}
    />
  );
}
