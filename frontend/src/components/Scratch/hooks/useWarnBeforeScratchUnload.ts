import * as api from "@/lib/api";
import { useWarnBeforeUnload } from "@/lib/hooks";

export default function useWarnBeforeScratchUnload(scratch: api.Scratch) {
    const userIsYou = api.useUserIsYou();
    const isSaved = api.useIsScratchSaved(scratch);
    const canSaveDirectly =
        userIsYou(scratch.owner) || api.isApiAgentOwned(scratch.owner);

    useWarnBeforeUnload(
        !isSaved,
        canSaveDirectly
            ? "You have not saved your changes to this scratch. Discard changes?"
            : "You have edited this scratch but not saved it in a fork. Discard changes?",
    );
}
